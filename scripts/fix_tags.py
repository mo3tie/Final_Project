from pathlib import Path
p = Path(r"c:\Users\User\grad\src\pages\PlateScan\PlateScan.jsx")
t = p.read_text(encoding="utf-8")
t = t.replace("<motion.div", "<div")
bad = "</" + "motion.div>"
t = t.replace(bad, "</motion.div>")
t = t.replace("</motion.div>", "</" + "div>")
p.write_text(t, encoding="utf-8")
print("fixed")
