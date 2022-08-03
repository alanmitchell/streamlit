from google.cloud import bigquery

client = bigquery.Client()

sql = """
SELECT 
  TIMESTAMP_TRUNC(ts, HOUR) as ts_hr,
  count(ts) as ct 
FROM `an-projects.things.gateway_reception` 
WHERE 
  ts > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 HOUR)
  AND gateway LIKE '%altermatt%'
GROUP BY ts_hr
ORDER BY ts_hr
"""

qj = client.query(sql)
for r in qj.result():
    print(r)
