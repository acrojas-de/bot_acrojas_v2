# -*- coding: utf-8 -*-

def classify_market_state(signal: dict) -> dict:
    radar = signal.get("radar", {})
    interpretation = str(signal.get("interpretation", "")).upper()
    strength = str(signal.get("strength", "")).upper()

    buy_15m = radar.get("15m") == "BUY"
    buy_1h = radar.get("1h") == "BUY"
    sell_15m = radar.get("15m") == "SELL"
    sell_1h = radar.get("1h") == "SELL"

    reasons = []

    if buy_15m and buy_1h:
        reasons.append("15m y 1h alineados al alza")
        if "BUY" in strength:
            reasons.append("Fuerza alcista detectada")
        return {
            "state": "TENDENCIA",
            "bias": "LONG",
            "reasons": reasons,
        }

    if sell_15m and sell_1h:
        reasons.append("15m y 1h alineados a la baja")
        if "SELL" in strength:
            reasons.append("Fuerza bajista detectada")
        return {
            "state": "TENDENCIA",
            "bias": "SHORT",
            "reasons": reasons,
        }

    if "INDECISO" in interpretation or "NEUTRAL" in strength:
        reasons.append("Interpretacion de indecision o fuerza neutral")
        return {
            "state": "RANGO",
            "bias": "MIXTO",
            "reasons": reasons,
        }

    reasons.append("Senal parcial sin confirmacion suficiente")
    return {
        "state": "TRANSICION",
        "bias": "MIXTO",
        "reasons": reasons,
    }

def detect_setup(signal: dict, market_context: dict) -> dict:
    radar = signal.get("radar", {})
    rsi_map = signal.get("rsi", {})
    trap = signal.get("trap", {})

    compression = signal.get("compression", {})

    # 🔥 PRIORIDAD 0: EMA50 FIRST TOUCH
    ema50_long = compression.get("ema50_touch_long", False)
    ema50_short = compression.get("ema50_touch_short", False)

    print("EMA50 LONG:", ema50_long)
    print("EMA50 SHORT:", ema50_short)

    if ema50_long:
        return {
            "detected": True,
            "setup_type": "EMA50_FIRST_TOUCH_LONG",
            "reasons": ["Primer toque EMA50 desde abajo"],
        }

    if ema50_short:
        return {
            "detected": True,
            "setup_type": "EMA50_FIRST_TOUCH_SHORT",
            "reasons": ["Primer toque EMA50 desde arriba"],
        }

    compression_long = compression.get("compression_long", False)
    compression_short = compression.get("compression_short", False)
    explosion_long = compression.get("explosion_long", False)
    explosion_short = compression.get("explosion_short", False)
    flag_active = compression.get("flag_active", False)
    flag_side = compression.get("flag_side", "NONE")

    trap_flag = trap.get("trap", False) if isinstance(trap, dict) else False

    reasons = []
    setup_type = "NONE"
    detected = False

    if explosion_long:
        reasons.append("Explosion alcista tras compresion")
        setup_type = "EXPLOSION_LONG"
        detected = True
        return {
            "detected": detected,
            "setup_type": setup_type,
            "reasons": reasons,
        }

    if explosion_short:
        reasons.append("Explosion bajista tras compresion")
        setup_type = "EXPLOSION_SHORT"
        detected = True
        return {
            "detected": detected,
            "setup_type": setup_type,
            "reasons": reasons,
        }

    if flag_active:
        reasons.append(f"Compresion tipo bandera detectada ({flag_side})")

    if compression_long:
        reasons.append("Compresion + ruptura alcista confirmada")
        setup_type = "COMPRESSION_LONG"
        detected = True
        return {
            "detected": detected,
            "setup_type": setup_type,
            "reasons": reasons,
        }

    if compression_short:
        reasons.append("Compresion + ruptura bajista confirmada")
        setup_type = "COMPRESSION_SHORT"
        detected = True
        return {
            "detected": detected,
            "setup_type": setup_type,
            "reasons": reasons,
        }


    if market_context["state"] == "TENDENCIA" and market_context["bias"] == "LONG":
        if radar.get("5m") == "BUY" and radar.get("15m") == "BUY" and radar.get("1h") == "BUY":
            reasons.append("Radar alineado en 5m, 15m y 1h para LONG")
            rsi_5m = rsi_map.get("5m")
            if rsi_5m is not None and 45 <= rsi_5m <= 68:
                reasons.append("RSI 5m en rango operativo LONG")
                if not trap_flag:
                    reasons.append("Sin trampa detectada")
                    setup_type = "LONG"
                    detected = True

    if market_context["state"] == "TENDENCIA" and market_context["bias"] == "SHORT":
        if radar.get("5m") == "SELL" and radar.get("15m") == "SELL" and radar.get("1h") == "SELL":
            reasons.append("Radar alineado en 5m, 15m y 1h para SHORT")
            rsi_5m = rsi_map.get("5m")
            if rsi_5m is not None and 32 <= rsi_5m <= 55:
                reasons.append("RSI 5m en rango operativo SHORT")
                if not trap_flag:
                    reasons.append("Sin trampa detectada")
                    setup_type = "SHORT"
                    detected = True

    return {
        "detected": detected,
        "setup_type": setup_type,
        "reasons": reasons,
    }


def validate_setup(signal: dict, market_context: dict, setup: dict) -> dict:
    reasons_yes = []
    reasons_no = []

    allowed_early_setups = (
        "COMPRESSION_LONG",
        "COMPRESSION_SHORT",
        "EXPLOSION_LONG",
        "EXPLOSION_SHORT",
        "EMA50_FIRST_TOUCH_LONG",
        "EMA50_FIRST_TOUCH_SHORT",
    )

    if market_context["state"] != "TENDENCIA":
        if setup["setup_type"] not in allowed_early_setups:
            reasons_no.append(f"Estado de mercado no operable: {market_context['state']}")
        else:
            reasons_yes.append("Setup valido fuera de tendencia principal")

    if market_context["bias"] == "MIXTO":
        if setup["setup_type"] not in allowed_early_setups:
            reasons_no.append("Sesgo mixto, sin direccion clara")

    if not setup["detected"]:
        reasons_no.append("No hay setup valido detectado")
    else:
        reasons_yes.extend(setup["reasons"])

    interpretation = str(signal.get("interpretation", "")).upper()
    if "INDECISO" in interpretation:
        if setup["setup_type"] not in allowed_early_setups:
            reasons_no.append("Interpretacion de mercado indeciso")

    trap = signal.get("trap", {})
    trap_flag = trap.get("trap", False) if isinstance(trap, dict) else False
    if trap_flag:
        reasons_no.append("Trampa detectada")

    valid = len(reasons_no) == 0

    return {
        "valid": valid,
        "reasons_yes": reasons_yes,
        "reasons_no": reasons_no,
    }


def build_operational_decision(signal: dict) -> dict:
    market_context = classify_market_state(signal)
    setup = detect_setup(signal, market_context)
    validation = validate_setup(signal, market_context, setup)

    decision = "ESPERAR"

    if validation["valid"] and setup["setup_type"] in (
        "LONG",
        "COMPRESSION_LONG",
        "EXPLOSION_LONG",
        "EMA50_FIRST_TOUCH_LONG",
    ):
        decision = "OPERAR LONG"

    elif validation["valid"] and setup["setup_type"] in (
        "SHORT",
        "COMPRESSION_SHORT",
        "EXPLOSION_SHORT",
        "EMA50_FIRST_TOUCH_SHORT",
    ):
        decision = "OPERAR SHORT"

    return {
        "market_state": market_context["state"],
        "bias": market_context["bias"],
        "context_reasons": market_context["reasons"],
        "setup_detected": setup["detected"],
        "setup_type": setup["setup_type"],
        "setup_reasons": setup["reasons"],
        "setup_valid": validation["valid"],
        "reasons_yes": validation["reasons_yes"],
        "reasons_no": validation["reasons_no"],
        "decision": decision,
    }