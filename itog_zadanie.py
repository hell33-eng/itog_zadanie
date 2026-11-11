"""Графический интерфейс Crypto Rates: кнопки монет, карточка курса."""

import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from api import AUTO_OPTIONS, COINS, fetch_prices


class CryptoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Crypto Rates (CoinPaprika)")
        self.root.geometry("620x460")
        self.root.minsize(560, 400)

        self._job_id = None
        self._selected = "btc-bitcoin"
        self._data = {}

        self._build_buttons_panel()
        self._build_info_panel()
        self._build_controls()
        self._build_status()

        self.refresh(silent=True)

    # ---------- левая панель: кнопки монет ----------

    def _build_buttons_panel(self):
        panel = tk.LabelFrame(self.root, text="Выберите монету", padx=8, pady=8)
        panel.grid(row=0, column=0, sticky="nsew", padx=8, pady=(10, 4))

        self.coin_buttons = {}
        self._btn_default_bg = None
        for coin_id, (name, ticker) in COINS.items():
            btn = tk.Button(
                panel,
                text=f"{name} ({ticker})",
                anchor="w",
                font=("Arial", 11),
                relief="raised",
                command=lambda cid=coin_id: self.select_coin(cid),
            )
            btn.pack(fill="x", pady=2)
            self.coin_buttons[coin_id] = btn
            if self._btn_default_bg is None:
                self._btn_default_bg = btn.cget("bg")

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)

    # ---------- правая панель: карточка с курсом ----------

    def _build_info_panel(self):
        panel = tk.LabelFrame(self.root, text="Курс", padx=12, pady=12)
        panel.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=(10, 4))

        self.name_label = tk.Label(panel, text="—", font=("Arial", 16, "bold"))
        self.name_label.pack(anchor="w")

        self.price_label = tk.Label(panel, text="— USD",
                                    font=("Consolas", 28, "bold"))
        self.price_label.pack(anchor="w", pady=(8, 4))

        self.change_label = tk.Label(panel, text="Изменение за 24 ч: —",
                                     font=("Arial", 12))
        self.change_label.pack(anchor="w")

        self.updated_label = tk.Label(panel, text="Данные пока не загружены",
                                      font=("Arial", 10), fg="gray")
        self.updated_label.pack(anchor="w", pady=(12, 0))

    # ---------- нижняя панель: кнопки управления ----------

    def _build_controls(self):
        panel = tk.Frame(self.root)
        panel.grid(row=1, column=0, columnspan=2, sticky="ew",
                   padx=8, pady=4)

        self.refresh_btn = tk.Button(
            panel, text="🔄 Обновить все курсы",
            font=("Arial", 11, "bold"),
            bg="#2f80ed", fg="white",
            activebackground="#1f6fd6", activeforeground="white",
            relief="raised", padx=12, pady=6,
            command=self.refresh,
        )
        self.refresh_btn.pack(side="left")

        auto_frame = tk.Frame(panel)
        auto_frame.pack(side="left", padx=(16, 0))

        tk.Label(auto_frame, text="Автообновление:").pack(side="left")
        self.auto_var = tk.StringVar(value="1 минута")
        combo = tk.OptionMenu(
            auto_frame, self.auto_var, *AUTO_OPTIONS,
            command=lambda _: self._schedule_refresh(),
        )
        combo.config(width=9)
        combo.pack(side="left", padx=(4, 0))

    def _build_status(self):
        self.status_label = tk.Label(self.root, anchor="w", text="Готово")
        self.status_label.grid(row=2, column=0, columnspan=2,
                               sticky="ew", padx=8, pady=(0, 8))

    # ---------- логика ----------

    def select_coin(self, coin_id: str):
        self._selected = coin_id
        self._highlight_selected()
        self._show_coin(coin_id)

    def _highlight_selected(self):
        for cid, btn in self.coin_buttons.items():
            if cid == self._selected:
                btn.config(bg="#d0e4fe", relief="sunken")
            else:
                btn.config(bg=self._btn_default_bg, relief="raised")

    def _show_coin(self, coin_id: str):
        name, ticker = COINS[coin_id]
        self.name_label.config(text=f"{name} ({ticker})")

        info = self._data.get(coin_id)
        if not info:
            self.price_label.config(text="нет данных")
            self.change_label.config(text="Изменение за 24 ч: —",
                                     fg="gray")
            return

        price = info.get("usd")
        change = info.get("usd_24h_change")

        price_str = (f"{price:,.2f} USD".replace(",", " ")
                     if price is not None else "—")
        self.price_label.config(text=price_str)

        if change is not None:
            if change > 0:
                self.change_label.config(
                    text=f"Изменение за 24 ч: +{change:.2f}% ▲", fg="#1a7f37")
            elif change < 0:
                self.change_label.config(
                    text=f"Изменение за 24 ч: {change:.2f}% ▼", fg="#c62828")
            else:
                self.change_label.config(
                    text="Изменение за 24 ч: 0.00%", fg="gray")

    def refresh(self, silent: bool = False):
        """Загружает курсы в отдельном потоке, чтобы окно не зависало."""
        self.refresh_btn.config(state="disabled")
        if not silent:
            self.status_label.config(text="Загрузка данных…")
        threading.Thread(target=self._load_data,
                         args=(silent,), daemon=True).start()

    def _load_data(self, silent: bool):
        try:
            data = fetch_prices()
            error = None
        except RuntimeError as e:
            data, error = None, str(e)
        self.root.after(0, lambda: self._apply_result(data, error, silent))

    def _apply_result(self, data, error, silent: bool):
        self.refresh_btn.config(state="normal")

        if error is not None:
            self.status_label.config(text=f"⚠ {error}")
            if not silent:
                messagebox.showerror("Ошибка сети", error)
            return

        self._data = data
        self._show_coin(self._selected)
        now = datetime.now().strftime("%H:%M:%S")
        self.updated_label.config(text=f"Обновлено в {now}")
        self.status_label.config(text=f"✓ Курсы загружены ({now})")
        self._schedule_refresh()

    # ---------- автообновление ----------

    def _schedule_refresh(self):
        if self._job_id is not None:
            self.root.after_cancel(self._job_id)
            self._job_id = None
        seconds = AUTO_OPTIONS[self.auto_var.get()]
        if seconds:
            self._job_id = self.root.after(seconds * 1000,
                                           lambda: self.refresh(silent=True))

