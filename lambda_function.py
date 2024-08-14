from client import aws_session

def list_all_available_metrics(namespace, metrics, account_number):
    session = aws_session(account_number, region="ap-southeast-1")
    cw = session.client("cloudwatch", region_name="ap-southeast-1")
    availMetrics = []
    response = cw.list_metrics(Namespace=namespace, MetricName=metrics, RecentlyActive="PT3H")
    availMetrics.extend(response["Metrics"])
    while "NextToken" in response:
        response = cw.list_metrics(Namespace=namespace, MetricName=metrics, RecentlyActive="PT3H", NextToken=response["NextToken"])
        # availMetrics = availMetrics + response["Metrics"]
        availMetrics.extend(response["Metrics"])
    result = []
    for item in availMetrics:
        tempDict = {}
        dimList = item.get("Dimensions")
        for iter in dimList:
            tempDict[iter["Name"]] = iter["Value"]
        result.append(tempDict)
    return result

def lambda_handler(event, context):
    metric_name = event.get("metric_name", "CPUUtilization")
    namespace = event.get("namespace", "AWS/EC2")
    threshold = event.get("threshold", 80)
    account_name = event.get("account_name", "FastDB")
    account_number = event.get("account_number", "003866745935")
    environment = event.get("environment", "training")
    region = event.get("region", "ap-southeast-3")
    
    session = aws_session(003866745935, region=region)
    cw = session.client("cloudwatch", region_name=region)
    
    instance_id_list = []
    
    availMetrics = list_all_available_metrics(namespace, metric_name, account_number)
    print(availMetrics)
    for metric in availMetrics:
        if metric.get("InstanceId"):
            instance_id_list.append(metric.get("InstanceId"))
    
    #Create alarms
    for instance in instance_id_list:
        alarm_name = f"{environment.upper()} {account_name.upper()} - {metric_name} - {instance}"
        
        try:
            paginator = cw.get_paginator('describe_alarms')
            response_iterator = paginator.paginate(AlarmNames=[alarm_name])
            for response in response_iterator:
                if len(response['MetricAlarms']) == 0:
                    cw.put_metric_alarm(
                        AlarmName=alarm_name,
                        ComparisonOperator="GreaterThanThreshold",
                        EvaluationPeriods=1,
                        Threshold=threshold,
                        ActionsEnabled=True,
                        AlarmActions=["arn:aws:sns:ap-southeast-3:003866745935:Training"],
                        Metrics=[
                            {
                                'Id': "getMetricData",
                                'AccountId': str(account_number),
                                'MetricStat': {
                                    'Metric': {
                                        'Namespace': namespace,
                                        'MetricName': metric_name,
                                        'Dimensions': [
                                            {
                                                'Name': 'InstanceId',
                                                'Value': instance
                                            },
                                        ]
                                    },
                                    "Period": 300,
                                    'Stat': 'Average',
                                    
                                },
                            }
                        ]
                    )
        except Exception as e:
            print(e)
    return
