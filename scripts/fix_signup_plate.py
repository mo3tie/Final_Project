from pathlib import Path

p = Path(__file__).resolve().parents[1] / "src/pages/Auth/Signup.jsx"
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
out = []
i = 0
while i < len(lines):
    if "form-group signup-plate-group" in lines[i]:
        out.append('                  <p className="signup-ai-plate-hint">{t("signup.aiPlateHint")}</p>\n')
        out.append("\n")
        while i < len(lines) and "{/* Vehicle license photo */}" not in lines[i]:
            i += 1
        continue
    out.append(lines[i])
    i += 1
p.write_text("".join(out), encoding="utf-8")
print("Updated Signup.jsx")
