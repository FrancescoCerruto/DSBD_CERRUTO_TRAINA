import json
import time
import requests
import pandas as pd
from flask import request
from project.models import create, delete, retrieve_sla
from project.Config import Config
from project import create_app

app = create_app()


@app.route('/create_slo', methods=['POST'])
def create_slo():
    metrics_name = request.json.get('metrics')
    label = request.json.get('label')
    max_value = request.json.get('max_value')

    if None in [metrics_name, label, max_value]:
        return "Required {metrics, label, max_value}}", 400

    # check if {metrics, label} exists
    metrics_required = {'metrics': metrics_name, 'label': label}
    if metrics_required not in Config.METRICS_ALLOWED:
        return "Metrics doesn't exists", 400

    result = create(metrics_name, label, max_value)
    if result == 0:
        return "SLO recorded successfully", 200
    return "SLO updated successfully", 200


@app.route('/delete_slo', methods=['POST'])
def delete_slo():
    metrics = request.json.get('metrics')
    label = request.json.get('label')

    if None in [metrics, label]:
        return "Required (metrics, label)", 400

    # check if {metrics, label} exists
    metrics_required = {'metrics': metrics, 'label': label}
    if metrics_required not in Config.METRICS_ALLOWED:
        return "Metrics doesn't exists", 400

    response_db = delete(metrics, label)
    if response_db == 0:
        return "SLO deleted successfully", 200
    else:
        return "SLO not exists", 400


@app.get("/status_sla")
def status_sla():
    sla = retrieve_sla()

    if not sla:
        return "Empty SLA", 200

    dictionary = []

    for slo in sla:
        metrics_name = slo["metrics"]
        label = slo["label"]
        max_value = float(slo["max"])

        # retrive all metrics of all job
        response = requests.get("http://{}:9090/api/v1/query?query={}".format(Config.PROMETHEUS_SERVER, metrics_name))
        all_job = json.loads(response.content)['data']['result']

        find = False
        for job in all_job:
            if job['metric']['job'] == label:
                find = True
                if float(job['value'][1]) > max_value:
                    dictionary.append({
                        'metrics': metrics_name,
                        'label': label,
                        'value': float(job['value'][1]),
                        'max_value_allowed': max_value,
                        'status': False
                    })
                else:
                    dictionary.append({
                        'metrics': metrics_name,
                        'label': label,
                        'value': job['value'][1],
                        'max_value_allowed': max_value,
                        'status': True
                    })
        if not find:
            dictionary.append({
                'metrics': metrics_name,
                'label': label,
                'value': "Not produced",
                'max_value_allowed': max_value,
            })

    return dictionary, 200


@app.get("/get_violation")
def get_violation():
    # range vector
    seconds = request.args.get("seconds")
    if None in [seconds]:
        return "required arguments seconds in [3600, 10800, 21600]"
    seconds = int(seconds)
    sla = retrieve_sla()

    if not sla:
        return "Empty SLA", 200

    dictionary = []

    for slo in sla:
        step = "15s"
        if slo['metrics'] == Config.KAFKA_METRICS and slo['label'] == Config.CRYPTO_LABEL:
            step = "10m"
        # download data
        data_frame = downloadTimeSerie(slo, seconds, step)

        # process
        if data_frame.empty:
            dictionary.append({
                'metrics': slo['metrics'],
                'label': slo['label'],
                'violation': 0
            })
        else:
            violation = 0
            for _, row in data_frame.iterrows():
                val = row[data_frame.columns[0]]
                if val > slo['max']:
                    violation = violation + 1
            dictionary.append({
                'metrics': slo['metrics'],
                'label': slo['label'],
                'violation': violation
            })
    return dictionary, 200


def downloadTimeSerie(slo, seconds, step):
    response = requests.get("http://{}:9090/api/v1/query_range?query={}"
                            "&start={}"
                            "&end={}"
                            "&step={}".format(Config.PROMETHEUS_SERVER,
                                              slo['metrics'],
                                              time.time() - seconds,
                                              time.time(),
                                              step))
    all_job = json.loads(response.content)['data']['result']
    result = []
    find = False
    for job in all_job:
        if job['metric']['job'] == slo['label']:
            find = True
            # (time, value)
            result = json.loads(response.content)['data']['result'][0]['values']
    if not find:
        pd.DataFrame({'A': []})

    # cast result json to pandas data frame
    df = pd.DataFrame(result, columns=['Time', 'Value'])
    df['Time'] = pd.to_datetime(df['Time'], unit='s')
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df = df.set_index('Time')
    return df


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
