import os, io, base64, sqlite3, json, time, subprocess, re
from pathlib import Path
from html import unescape
import requests
from PIL import Image, ImageOps

FORMATS = {"horizontal": (1280,720), "vertical": (720,1280), "quadrado": (1024,1024)}
class MediaEngine:
    def __init__(self, cache="media_cache.sqlite"):
        self.db = sqlite3.connect(cache)
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, ts REAL, data TEXT)")
        self.http = requests.Session()
        self.http.headers["User-Agent"] = "ViralRadarMediaTest/1.0 (https://github.com/Cidb67/viralradar-scheduler-teste)"
    def generate(self, prompt, orientation, providers=("klein","schnell")):
        w,h = FORMATS[orientation]
        for provider in providers:
            try:
                account=os.environ["CLOUDFLARE_ACCOUNT_ID"]
                token=os.environ["CLOUDFLARE_API_TOKEN"]
                model={"klein":"flux-2-klein-4b","schnell":"flux-1-schnell"}[provider]
                url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/black-forest-labs/{model}"
                args={"files":{k:(None,str(v)) for k,v in {"prompt":prompt,"width":w,"height":h}.items()}} if provider=="klein" else {"json":{"prompt":prompt,"steps":4}}
                r=self.http.post(url,headers={"Authorization":"Bearer "+token},timeout=120,**args)
                print("IMAGE",provider,r.status_code,flush=True)
                if r.status_code in (401,403,429): raise PermissionError("Cloudflare access or quota")
                r.raise_for_status()
                raw=r.content if r.headers.get("Content-Type","").startswith("image/") else base64.b64decode(r.json()["result"]["image"])
                im=Image.open(io.BytesIO(raw)); im.load()
                original=im.size
                im=ImageOps.fit(im.convert("RGB"),(w,h))
                return im,{"provider":provider,"native_size":original,"size":im.size,"usage":"unverified"}
            except PermissionError:
                raise
            except Exception as e:
                print("IMAGE FAILED",provider,type(e).__name__,flush=True)
        raise RuntimeError("No image provider available")
    def pixabay(self, query, kind, orientation):
        key=json.dumps([query,kind,orientation])
        row=self.db.execute("SELECT ts,data FROM cache WHERE key=?",(key,)).fetchone()
        if row and time.time()-row[0]<86400:
            return json.loads(row[1])
        params={"key":os.environ["PIXABAY_API_KEY"],"q":query,"safesearch":"true","per_page":20}
        if kind=="image":
            params["image_type"]="photo"
            if orientation!="quadrado": params["orientation"]=orientation
        else: params["video_type"]="film"
        r=self.http.get("https://pixabay.com/api/"+("videos/" if kind=="video" else ""),params=params,timeout=30)
        print("PIXABAY",r.status_code,flush=True)
        if not r.ok: raise RuntimeError("Pixabay HTTP "+str(r.status_code))
        result=[]
        for item in r.json().get("hits",[]):
            v=item.get("videos",{}).get("medium",{}) if kind=="video" else {}
            w,h=v.get("width",item.get("imageWidth",0)),v.get("height",item.get("imageHeight",0))
            url=v.get("url") if kind=="video" else item.get("largeImageURL")
            if w and h and url and self.matches(w,h,orientation):
                result.append(dict(provider="Pixabay",url=url,source=item["pageURL"],author=item.get("user",""),license="Pixabay Content License",license_url="https://pixabay.com/service/license-summary/",width=w,height=h))
        self.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)",(key,time.time(),json.dumps(result))); self.db.commit()
        return result
    @staticmethod
    def matches(w,h,o):
        return w>h if o=="horizontal" else h>w if o=="vertical" else .9<=w/h<=1.1
    def wikimedia(self,query,kind,orientation):
        r=self.http.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","generator":"search","gsrsearch":query+" filetype:"+("bitmap" if kind=="image" else "video"),"gsrnamespace":6,"gsrlimit":20,"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","format":"json","formatversion":2},timeout=40)
        r.raise_for_status()
        result=[]
        for p in r.json().get("query",{}).get("pages",[]):
            i=p.get("imageinfo",[{}])[0]; m=i.get("extmetadata",{})
            def field(k): return unescape(re.sub("<[^>]+>","",m.get(k,{}).get("value",""))).strip()
            lic=field("LicenseShortName"); author=field("Artist"); w,h=i.get("width",0),i.get("height",0)
            if lic not in ("CC0","Public domain","CC BY 2.0","CC BY 2.5","CC BY 3.0","CC BY 4.0"): continue
            if lic.startswith("CC BY") and (not author or not field("LicenseUrl")): continue
            if w and h and self.matches(w,h,orientation) and i.get("url") and i.get("descriptionurl"):
                result.append(dict(provider="Wikimedia Commons",url=i["url"],source=i["descriptionurl"],author=author,license=lic,license_url=field("LicenseUrl"),width=w,height=h,title=p["title"]))
        return result
    def search(self,query,kind,orientation,providers=("pixabay","wikimedia")):
        for p in providers:
            try:
                results=getattr(self,p)(query,kind,orientation)
                if results: return results
            except Exception as e: print("SEARCH FAILED",p,type(e).__name__,flush=True)
        return []
    def prepare_video(self,source,destination,orientation,seconds=5):
        w,h=FORMATS[orientation]
        subprocess.run(["ffmpeg","-v","error","-y","-i",str(source),"-t",str(seconds),"-map","0:v:0","-an","-vf",f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(destination)],check=True,timeout=120)
