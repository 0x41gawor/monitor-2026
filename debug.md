W `systemd` zdrowie takiego **batch joba (oneshot + timer)** sprawdza się na trzech poziomach:

1. **czy timer działa i kiedy odpali**
2. **czy service wykonał się ostatnio poprawnie**
3. **logi z wykonania**

Poniżej masz dokładny workflow diagnostyczny.

---

# 1. Sprawdź timer

Najpierw sprawdzamy czy timer w ogóle jest aktywny.

```bash
systemctl status monitor.timer
```

Przykładowy wynik:

```
● monitor.timer - Run Monitor-2026 every day at 11:05
     Loaded: loaded (/etc/systemd/system/monitor.timer; enabled)
     Active: active (waiting)
    Trigger: Mon 2026-03-02 11:05:00 CET
   Triggers: ● monitor.service
```

Najważniejsze pola:

| Pole                       | Znaczenie                 |
| -------------------------- | ------------------------- |
| `Active: active (waiting)` | timer działa              |
| `Trigger:`                 | kiedy odpali następny run |
| `Triggers:`                | jaki service uruchomi     |

---

## Lista wszystkich timerów

Bardzo wygodne:

```bash
systemctl list-timers
```

lub tylko Twój:

```bash
systemctl list-timers monitor.timer
```

Przykład:

```
NEXT                        LEFT      LAST                        PASSED UNIT           ACTIVATES
Mon 2026-03-02 11:05:00     20h left  Sun 2026-03-01 11:05:01     3h ago monitor.timer  monitor.service
```

To jest **najlepszy health check** dla timerów.

---

# 2. Sprawdź service (czy run był OK)

Timer odpala:

```
monitor.service
```

Sprawdzasz:

```bash
systemctl status monitor.service
```

Jeśli ostatni run był OK zobaczysz np:

```
● monitor.service - Monitor-2026 daily ingestion job
     Loaded: loaded (/etc/systemd/system/monitor.service)
     Active: inactive (dead)
   Main PID: 1234 (code=exited, status=0/SUCCESS)
```

Najważniejsze:

| status             | znaczenie                   |
| ------------------ | --------------------------- |
| `status=0/SUCCESS` | job zakończył się poprawnie |
| `status=1/FAILURE` | coś się wywaliło            |

---

# 3. Logi joba

Masz w unit:

```
StandardOutput=journal
StandardError=journal
```

więc wszystko idzie do `journalctl`.

### ostatni run

```bash
journalctl -u monitor.service -n 50
```

### logi z dzisiaj

```bash
journalctl -u monitor.service --since today
```

### logi z konkretnego dnia

```bash
journalctl -u monitor.service --since "2026-03-01"
```

---

# 4. Ręczne odpalenie joba

Super przy debugowaniu.

```bash
systemctl start monitor.service
```

Potem:

```
systemctl status monitor.service
```

---

# 5. Czy timer jest włączony

Sprawdź czy nie zapomniałeś enable:

```bash
systemctl is-enabled monitor.timer
```

Powinno być:

```
enabled
```

Jeśli nie:

```bash
systemctl enable monitor.timer
systemctl start monitor.timer
```

---

# 6. Najlepszy "health check" dla cron-like jobów

Ja zwykle używam jednego polecenia:

```bash
systemctl list-timers monitor.timer
```

bo od razu widzisz:

* kiedy był **LAST run**
* czy timer działa
* kiedy będzie **NEXT run**

---

# 7. Bardzo dobra praktyka (polecam)

Dodaj timeout, żeby job nie wisiał.

```
[Service]
TimeoutStartSec=15min
```

---

# 8. Jeszcze lepszy monitoring (opcjonalnie)

Możesz zrobić **health check w stylu SRE**:

```
systemctl show monitor.service --property=Result
```

wynik:

```
Result=success
```

lub

```
Result=exit-code
```

---

# 9. Jeśli chcesz mieć monitoring jak w produkcji

Możesz zrobić prosty checker:

```bash
systemctl show monitor.service --property=ExecMainStatus
```

`0` = success
