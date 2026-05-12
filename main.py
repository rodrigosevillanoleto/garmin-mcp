import os
import json
from datetime import date, timedelta
from flask import Flask, request, jsonify, Response
from garminconnect import Garmin

app = Flask(__name__)

GARMIN_EMAIL = os.environ.get("GARMIN_EMAIL")
GARMIN_PASSWORD = os.environ.get("GARMIN_PASSWORD")
AUTH_KEY = os.environ.get("AUTH_KEY")

_garmin_client = None

def get_client():
    global _garmin_client
    if _garmin_client is None:
        _garmin_client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
        _garmin_client.login()
    return _garmin_client

def safe_call(fn, *args, **kwargs):
    global _garmin_client
    try:
        return fn(*args, **kwargs)
    except Exception:
        _garmin_client = None
        client = get_client()
        return fn(*args, **kwargs)

TOOLS = [
    {
        "name": "get_activities",
        "description": "Lista as atividades mais recentes. Parametro: limit (int, padrao 10).",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}}
        }
    },
    {
        "name": "get_activities_by_date",
        "description": "Atividades em um intervalo de datas. Parametros: start_date e end_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_activity_details",
        "description": "Metricas detalhadas de uma atividade. Parametro: activity_id.",
        "inputSchema": {
            "type": "object",
            "properties": {"activity_id": {"type": "string"}},
            "required": ["activity_id"]
        }
    },
    {
        "name": "get_activity_splits",
        "description": "Splits de uma atividade. Parametro: activity_id.",
        "inputSchema": {
            "type": "object",
            "properties": {"activity_id": {"type": "string"}},
            "required": ["activity_id"]
        }
    },
    {
        "name": "get_activity_hr_zones",
        "description": "Tempo em cada zona de FC. Parametro: activity_id.",
        "inputSchema": {
            "type": "object",
            "properties": {"activity_id": {"type": "string"}},
            "required": ["activity_id"]
        }
    },
    {
        "name": "get_training_plans",
        "description": "Lista todos os planos de treino.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_workouts",
        "description": "Lista os treinos salvos.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_calendar",
        "description": "Calendario de treinos programados. Parametros: year (int) e month (int, 1-12).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "month": {"type": "integer"}
            },
            "required": ["year", "month"]
        }
    },
    {
        "name": "get_vo2max",
        "description": "VO2 Max de corrida e ciclismo. Parametro opcional: target_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_training_status",
        "description": "Status de treinamento atual.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_training_readiness",
        "description": "Prontidao para treinar. Parametro opcional: target_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_personal_records",
        "description": "Recordes pessoais (5K, 10K, meia, maratona, etc).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_race_predictions",
        "description": "Previsao de tempo para 5K, 10K, meia e maratona.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_lactate_threshold",
        "description": "Limiar de lactato: FC e ritmo.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_daily_summary",
        "description": "Resumo diario completo: passos, calorias totais e ativas, distancia, andares, minutos ativos, FC repouso. Parametro opcional: target_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_daily_steps_range",
        "description": "Passos diarios em um intervalo de datas. Parametros: start_date e end_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_hydration",
        "description": "Hidratacao para uma data. Parametro opcional: target_date (YYYY-MM-DD).",
        "inputSchema": {
            "type": "object",
            "properties": {"target_date": {"type": "string"}}
        }
    },
    {
        "name": "get_endurance_score",
        "description": "Endurance Score.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_hill_score",
        "description": "Hill Score.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]

def call_tool(name, args):
    client = get_client()
    args = args or {}
    today = date.today().isoformat()

    if name == "get_activities":
        limit = args.get("limit", 10)
        return safe_call(client.get_activities, 0, limit)

    if name == "get_activities_by_date":
        return safe_call(client.get_activities_by_date, args["start_date"], args["end_date"])

    if name == "get_activity_details":
        return safe_call(client.get_activity, args["activity_id"])

    if name == "get_activity_splits":
        return safe_call(client.get_activity_splits, args["activity_id"])

    if name == "get_activity_hr_zones":
        return safe_call(client.get_activity_hr_in_timezones, args["activity_id"])

    if name == "get_training_plans":
        return safe_call(client.get_training_plans)

    if name == "get_workouts":
        return safe_call(client.get_workouts)

    if name == "get_calendar":
        return safe_call(client.get_calendar, args["year"], args["month"])

    if name == "get_vo2max":
        target = args.get("target_date", today)
        return safe_call(client.get_max_metrics, target)

    if name == "get_training_status":
        return safe_call(client.get_training_status, today)

    if name == "get_training_readiness":
        target = args.get("target_date", today)
        return safe_call(client.get_training_readiness, target)

    if name == "get_personal_records":
        return safe_call(client.get_personal_record)

    if name == "get_race_predictions":
        return safe_call(client.get_race_predictions)

    if name == "get_lactate_threshold":
        return safe_call(client.get_lactate_threshold)

    if name == "get_daily_summary":
        target = args.get("target_date", today)
        return safe_call(client.get_stats_and_body, target)

    if name == "get_daily_steps_range":
        return safe_call(client.get_daily_steps, args["start_date"], args["end_date"])

    if name == "get_hydration":
        target = args.get("target_date", today)
        return safe_call(client.get_hydration_data, target)

    if name == "get_endurance_score":
        return safe_call(client.get_endurance_score, today)

    if name == "get_hill_score":
        return safe_call(client.get_hill_score, today)

    raise ValueError("Ferramenta desconhecida: " + name)

def json_rpc(id_, result=None, error=None):
    body = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        body["error"] = error
    else:
        body["result"] = result
    return jsonify(body)

@app.route("/", methods=["GET"])
def index():
    key = request.args.get("key")
    if not AUTH_KEY or key != AUTH_KEY:
        return Response("Unauthorized", status=401)
    return Response("Garmin MCP server is running.", status=200)

@app.route("/", methods=["POST"])
def mcp():
    key = request.args.get("key")
    if not AUTH_KEY or key != AUTH_KEY:
        return Response("Unauthorized", status=401)

    try:
        payload = request.get_json(force=True)
    except Exception:
        return json_rpc(None, error={"code": -32700, "message": "Parse error"})

    id_ = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    try:
        if method == "initialize":
            return json_rpc(id_, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "garmin-mcp", "version": "1.1.0"}
            })

        if method == "tools/list":
            return json_rpc(id_, {"tools": TOOLS})

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            data = call_tool(tool_name, tool_args)
            text = json.dumps(data, default=str, ensure_ascii=False)
            return json_rpc(id_, {"content": [{"type": "text", "text": text}]})

        if method == "notifications/initialized":
            return Response(status=204)

        return json_rpc(id_, error={"code": -32601, "message": "Method not found"})

    except Exception as e:
        return json_rpc(id_, error={"code": -32603, "message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
