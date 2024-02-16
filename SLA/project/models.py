from project import db


class Metrics(db.Document):
    metrics = db.StringField()
    label = db.StringField()
    max = db.FloatField()


# insert new slo
def create(metrics_name, label_name, max_value):
    # check if exists
    record = Metrics.objects(metrics=metrics_name, label=label_name).first()
    if not record:
        Metrics(metrics=metrics_name, label=label_name, max=max_value).save()
        return 0
    else:
        record.delete()
        Metrics(metrics=metrics_name, label=label_name, max=max_value).save()
        return 1


# delete slo
def delete(metrics_name, label_name):
    record = Metrics.objects(metrics=metrics_name, label=label_name).first()
    if record:
        record.delete()
        return 0
    else:
        return -1


# retrive all slo
def retrieve_sla():
    return Metrics.objects()