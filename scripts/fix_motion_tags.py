from pathlib import Path

root = Path(__file__).resolve().parents[1]
for rel in [
    "src/pages/Profile & settings/AddVehicle/AddVehicle.jsx",
]:
    p = root / rel
    t = p.read_text(encoding="utf-8")
    t = t.replace("<motion.div", "<div")
    t = t.replace("</motion.div>", "</motion.div>")
    t = t.replace("</motion.div>", "</" + "motion.div>"[2:])  # broken
    bad = "</" + "motion.div>"
    t = t.replace(bad, "</div>")
    p.write_text(t, encoding="utf-8")
    print("fixed", rel)
