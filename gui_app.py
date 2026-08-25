from __future__ import annotations

import threading
import tkinter as tk

import customtkinter as ctk

import config
from settings_store import load_settings, save_settings

PLATFORMS = [
    ("baemin", "배달의민족", "#2AC1BC"),
    ("coupang", "쿠팡이츠", "#3478F6"),
    ("yogiyo", "요기요", "#FA0050"),
    ("ddangyo", "땡겨요", "#FF7A00"),
    ("special", "배달특급", "#7B61FF"),
]
TONES = [
    ("kind", "친절/감성"),
    ("polite", "정중/깔끔"),
    ("firm", "악플 단호 대처"),
    ("short", "1줄 초간단"),
]


class Dashboard(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("배달 리뷰 AI 대시보드")
        self.geometry("1080x820")
        self.minsize(960, 720)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.font = ctk.CTkFont(family="Malgun Gothic", size=13)
        self.font_b = ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold")
        self.running = False
        self.pw_shown: dict[str, bool] = {}
        self.vars: dict = {}
        self.status: dict[str, ctk.CTkLabel] = {}
        self.tone_var = tk.StringVar(value="polite")
        self.mode_var = tk.StringVar(value="show")
        self._build()
        self._load()

    def _build(self) -> None:
        self.configure(fg_color="#F4F5F7")
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(18, 8))
        ctk.CTkLabel(header, text="리뷰 답글 통합 설정", font=ctk.CTkFont(family="Malgun Gothic", size=22, weight="bold"), text_color="#191F28").pack(anchor="w")
        ctk.CTkLabel(header, text="계정과 AI 톤을 저장한 뒤 한 번에 실행하세요", font=self.font, text_color="#8B95A1").pack(anchor="w")

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=4)

        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x")
        for i, (key, name, color) in enumerate(PLATFORMS):
            card = self._platform_card(grid, key, name, color)
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=6)
        grid.grid_columnconfigure((0, 1), weight=1)

        ai = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=18)
        ai.pack(fill="x", padx=6, pady=8)
        inner = ctk.CTkFrame(ai, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(inner, text="AI · 매장 스타일", font=self.font_b, text_color="#191F28").pack(anchor="w")

        ctk.CTkLabel(inner, text="Gemini API 키", font=self.font, text_color="#8B95A1").pack(anchor="w", pady=(10, 4))
        self.api_var = tk.StringVar()
        self.api_entry = ctk.CTkEntry(inner, textvariable=self.api_var, show="*", height=40, font=self.font)
        self.api_entry.pack(fill="x")
        self.api_hint = ctk.CTkLabel(inner, text="", font=self.font, text_color="#8B95A1")
        self.api_hint.pack(anchor="w")

        ctk.CTkLabel(inner, text="답글 톤앤매너", font=self.font, text_color="#8B95A1").pack(anchor="w", pady=(8, 6))
        tones = ctk.CTkFrame(inner, fg_color="transparent")
        tones.pack(fill="x")
        for val, label in TONES:
            ctk.CTkRadioButton(tones, text=label, variable=self.tone_var, value=val, font=self.font).pack(side="left", padx=(0, 14))

        ctk.CTkLabel(inner, text="매장 공통 지침", font=self.font, text_color="#8B95A1").pack(anchor="w", pady=(10, 4))
        self.guide = ctk.CTkTextbox(inner, height=78, font=self.font)
        self.guide.pack(fill="x")

        run = ctk.CTkFrame(body, fg_color="#FFFFFF", corner_radius=18)
        run.pack(fill="x", padx=6, pady=6)
        r_in = ctk.CTkFrame(run, fg_color="transparent")
        r_in.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(r_in, text="실행", font=self.font_b).pack(anchor="w")
        mode = ctk.CTkFrame(r_in, fg_color="transparent")
        mode.pack(anchor="w", pady=8)
        ctk.CTkRadioButton(mode, text="브라우저 화면 보면서 실행", variable=self.mode_var, value="show", font=self.font).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(mode, text="헤드리스 백그라운드", variable=self.mode_var, value="hide", font=self.font).pack(side="left")

        btns = ctk.CTkFrame(r_in, fg_color="transparent")
        btns.pack(fill="x", pady=6)
        ctk.CTkButton(btns, text="설정 저장", height=42, fg_color="#E8F3FF", text_color="#3182F6", hover_color="#D6E8FF", font=self.font_b, command=self.save).pack(side="left", padx=(0, 8))
        self.start_btn = ctk.CTkButton(
            btns, text="전체 플랫폼 자동 리뷰 달기 시작", height=46,
            fg_color="#3182F6", hover_color="#1B64DA", font=self.font_b, command=self.start_run
        )
        self.start_btn.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(r_in, text="실시간 진행", font=self.font, text_color="#8B95A1").pack(anchor="w", pady=(10, 4))
        self.console = ctk.CTkTextbox(r_in, height=160, font=ctk.CTkFont(family="Consolas", size=12), fg_color="#191F28", text_color="#E5E8EB")
        self.console.pack(fill="x")
        self.console.insert("end", "준비가 되면 저장 후 실행하세요.\n")
        self.console.configure(state="disabled")

    def _platform_card(self, parent, key: str, name: str, color: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=18, border_width=2, border_color=color)
        pad = ctk.CTkFrame(card, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=14, pady=12)
        top = ctk.CTkFrame(pad, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=name, font=self.font_b, text_color=color).pack(side="left")
        enabled = tk.BooleanVar(value=True)
        self.vars[f"{key}_on"] = enabled
        ctk.CTkSwitch(top, text="ON", variable=enabled, font=self.font, progress_color=color).pack(side="right")

        id_var = tk.StringVar()
        pw_var = tk.StringVar()
        self.vars[f"{key}_id"] = id_var
        self.vars[f"{key}_pw"] = pw_var
        ctk.CTkLabel(pad, text="아이디", font=self.font, text_color="#8B95A1").pack(anchor="w", pady=(8, 2))
        ctk.CTkEntry(pad, textvariable=id_var, height=36, font=self.font).pack(fill="x")
        ctk.CTkLabel(pad, text="비밀번호", font=self.font, text_color="#8B95A1").pack(anchor="w", pady=(8, 2))
        row = ctk.CTkFrame(pad, fg_color="transparent")
        row.pack(fill="x")
        pw_entry = ctk.CTkEntry(row, textvariable=pw_var, show="*", height=36, font=self.font)
        pw_entry.pack(side="left", fill="x", expand=True)
        self.vars[f"{key}_pw_entry"] = pw_entry
        self.pw_shown[key] = False
        ctk.CTkButton(row, text="👁", width=42, height=36, fg_color="#F2F4F6", text_color="#191F28", hover_color="#E5E8EB", command=lambda k=key: self.toggle_pw(k)).pack(side="left", padx=(6, 0))

        foot = ctk.CTkFrame(pad, fg_color="transparent")
        foot.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(foot, text="로그인 테스트", width=110, height=32, fg_color=color, hover_color=color, font=self.font, command=lambda k=key: self.login_test(k)).pack(side="left")
        st = ctk.CTkLabel(foot, text="미저장", font=self.font, text_color="#8B95A1")
        st.pack(side="right")
        self.status[key] = st
        return card

    def toggle_pw(self, key: str) -> None:
        self.pw_shown[key] = not self.pw_shown[key]
        self.vars[f"{key}_pw_entry"].configure(show="" if self.pw_shown[key] else "*")

    def collect(self) -> dict:
        data = load_settings()
        data["gemini_api_key"] = self.api_var.get().strip()
        data["reply_tone"] = self.tone_var.get()
        data["store_guide"] = self.guide.get("1.0", "end").strip()
        data["headful"] = self.mode_var.get() != "hide"
        for key, _, _ in PLATFORMS:
            data["platforms"][key] = {
                "enabled": bool(self.vars[f"{key}_on"].get()),
                "id": self.vars[f"{key}_id"].get().strip(),
                "pw": self.vars[f"{key}_pw"].get(),
            }
        return data

    def _load(self) -> None:
        data = load_settings()
        self.api_var.set(data.get("gemini_api_key", ""))
        self.tone_var.set(data.get("reply_tone", "polite"))
        self.mode_var.set("show" if data.get("headful", True) else "hide")
        self.guide.delete("1.0", "end")
        self.guide.insert("1.0", data.get("store_guide", ""))
        for key, _, _ in PLATFORMS:
            row = (data.get("platforms") or {}).get(key) or {}
            self.vars[f"{key}_on"].set(bool(row.get("enabled", True)))
            self.vars[f"{key}_id"].set(row.get("id", ""))
            self.vars[f"{key}_pw"].set(row.get("pw", ""))
            self.status[key].configure(text="저장됨" if row.get("id") else "미저장", text_color="#00C471" if row.get("id") else "#8B95A1")
        self._validate_api()

    def _validate_api(self) -> bool:
        key = self.api_var.get().strip()
        ok = len(key) >= 20
        self.api_hint.configure(text="키가 유효해 보입니다." if ok else "API 키를 붙여넣으세요. (20자 이상)", text_color="#00C471" if ok else "#8B95A1")
        return ok

    def save(self) -> None:
        save_settings(self.collect())
        config.reload()
        self._validate_api()
        for key, _, _ in PLATFORMS:
            has = bool(self.vars[f"{key}_id"].get().strip())
            self.status[key].configure(text="계정 저장됨" if has else "미저장", text_color="#00C471" if has else "#8B95A1")
        self.append_log("설정을 암호화해 로컬에 저장했습니다.")

    def append_log(self, msg: str) -> None:
        def _write() -> None:
            self.console.configure(state="normal")
            self.console.insert("end", msg + "\n")
            self.console.see("end")
            self.console.configure(state="disabled")
        self.after(0, _write)

    def login_test(self, key: str) -> None:
        self.save()
        self.append_log(f"로그인 테스트: {key}")

        def work() -> None:
            from main import test_login
            ok = test_login(key, self.append_log)
            color = "#00C471" if ok else "#F04452"
            text = "로그인 테스트 성공" if ok else "로그인 테스트 실패"
            self.after(0, lambda: self.status[key].configure(text=text, text_color=color))

        threading.Thread(target=work, daemon=True).start()

    def start_run(self) -> None:
        if self.running:
            return
        self.save()
        if not self._validate_api():
            self.append_log("Gemini API 키를 먼저 저장하세요.")
            return
        self.running = True
        self.start_btn.configure(state="disabled", text="실행 중...")
        self.append_log("전체 플랫폼 자동 리뷰 작성을 시작합니다.")

        def work() -> None:
            from main import run_all
            try:
                run_all(self.append_log)
            finally:
                self.running = False
                self.after(0, lambda: self.start_btn.configure(state="normal", text="전체 플랫폼 자동 리뷰 달기 시작"))

        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    Dashboard().mainloop()
