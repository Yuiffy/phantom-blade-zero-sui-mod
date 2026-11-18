"""Orthographic, depth-tested rear views and safety-lining exposure on replayed poses."""
from pathlib import Path

import numpy as np
from numba import njit
from PIL import Image, ImageDraw
from build import WORK, PREVIOUS, STAGE, read, write, decode


@njit
def raster(points, triangles, size):
    depth = np.full((size, size), -np.inf)
    ids = np.full((size, size), -1)
    bary = np.zeros((size, size, 2), dtype=np.float32)
    for i, tri in enumerate(triangles):
        a, b, c = points[tri[0]], points[tri[1]], points[tri[2]]
        u, v = b - a, c - a
        det = u[0]*v[1] - u[1]*v[0]
        if abs(det) < 1e-8:
            continue
        for y in range(max(0, int(np.ceil(min(a[1],b[1],c[1])))), min(size, int(np.floor(max(a[1],b[1],c[1])))+1)):
            for x in range(max(0, int(np.ceil(min(a[0],b[0],c[0])))), min(size, int(np.floor(max(a[0],b[0],c[0])))+1)):
                dx, dy = x-a[0], y-a[1]
                t, s = (dx*v[1]-dy*v[0])/det, (u[0]*dy-u[1]*dx)/det
                if t >= 0 and s >= 0 and t+s <= 1:
                    z = a[2] + t*u[2] + s*v[2]
                    if z > depth[y,x]:
                        depth[y,x], ids[y,x] = z, i
                        bary[y,x,0], bary[y,x,1] = t,s
    return ids, bary


def view(frame, faces, mats, angle, size, height):
    theta = np.radians(angle)
    toward = np.array([np.sin(theta), -np.cos(theta), .10])
    toward /= np.linalg.norm(toward)
    right = np.array([np.cos(theta), np.sin(theta), 0])
    down = np.cross(right, toward)
    projected = (frame - [0, -4, height]) @ np.array([right, down, toward]).T
    projected[:, :2] = projected[:, :2] * (size/75) + size/2
    ids, bary = raster(projected, faces, size)
    return ids, bary, int(np.sum((ids >= 0) & (mats[ids] == 8)))


def picture(arrays, frame, angle, height, textures, uv):
    faces, mats = arrays["faces"], arrays["materials"]
    ids, bary, count = view(frame, faces, mats, angle, 340, height)
    rgb = np.full((340,340,3), 213, dtype=np.uint8)
    for mat in np.unique(mats):
        selected = (ids >= 0) & (mats[ids] == mat)
        corners = uv[faces[ids[selected]]]
        t = bary[selected]
        coords = corners[:,0] + (corners[:,1]-corners[:,0])*t[:,0,None] + (corners[:,2]-corners[:,0])*t[:,1,None]
        texture = textures[mat]
        ix = np.floor((coords % 1) * [texture.shape[1],texture.shape[0]]).astype(int)
        rgb[selected] = texture[ix[:,1],ix[:,0]]
    return Image.fromarray(rgb)


def check():
    output = WORK / "preview"
    output.mkdir(exist_ok=True)
    sources = read(PREVIOUS.parent / "outfit-patterns-v1/preview-materials.json")["jk"]
    textures = []
    for src in sources:
        path = Path(src["path"])
        if path.name == "jk-before.png":
            path = path.with_name("jk-after.png")
        with Image.open(path) as image:
            textures.append(np.array(image.convert("RGB").resize((1024,1024))))
    native_uv = np.load(PREVIOUS.parent / "jk-face-shape-v1/final.npz")["uv"][:,0]
    rows = []
    for path in sorted((WORK / "motion").glob("*-surface.npz")):
        with np.load(path) as data:
            frames, times = data["frames"], data["times"]
            faces, mats = data["faces"], data["materials"]
            quiet = (abs(times)<.01) | ((times >= 0) & (times % 5 >= .5) & (times % 5 <= 1.001) & (times > 5))
            # Recovery windows end at t=6,11,16; the first second is static too.
            values = [view(frame, faces, mats, 0, 200, 98)[2] for frame in frames]
            rows.append(dict(file=path.name, quiet_max_pixels=int(np.max(np.array(values)[quiet])), all_max_pixels=max(values), image_size=200))
    # Stress isolates cloth lifting: apply the same large displacement to the
    # physical input before blending. It does not purport to recreate the game pose.
    cases = [("Stand","jog",0,0),("Run","jog",2.67,0),("Recovered","jog",15.5,0),("Crouch","crouch",2,0),("Lift stress","jog",0,32)]
    stress_counts = {}
    for name, directory, document in [("previous",PREVIOUS/STAGE,"before"),("candidate",WORK/"motion","final")]:
        _,_,_,detail = decode(read(WORK/"native"/(document+".json")))
        skirt = detail["sections"][14]
        weights = 1-np.array(skirt["cloth_maps"][0]["source"])[:,3]/65535
        sheet = Image.new("RGB",(340*len(cases),2*370),"white")
        draw = ImageDraw.Draw(sheet)
        for i,(label,profile,time,lift) in enumerate(cases):
            with np.load(directory/f"{profile}-60-surface.npz") as arrays:
                index = np.argmin(abs(arrays["times"]-time))
                frame = arrays["frames"][index].copy()
                ix = np.searchsorted(arrays["ids"], np.arange(skirt["base_vertex"],skirt["base_vertex"]+skirt["vertices"]))
                frame[ix,2] += weights*lift
                height = 94 if profile=="crouch" else 98
                for j,angle in enumerate([0,38]):
                    panel = picture(arrays,frame,angle,height,textures,native_uv[arrays["ids"]])
                    sheet.paste(panel,(340*i,370*j+25))
                    draw.text((340*i+6,370*j+6),f"{label}  {angle} deg",fill="black")
                    if lift:
                        stress_counts[f"{name}-{angle}"] = view(frame,arrays["faces"],arrays["materials"],angle,200,height)[2]
        sheet.save(output / (name+".jpg"),quality=91)
    write(WORK/"coverage.json",dict(replays=rows,stress_pixels=stress_counts,stress_input_up_cm=32,material=8))
    print(rows,stress_counts,flush=True)


if __name__ == "__main__":
    check()
