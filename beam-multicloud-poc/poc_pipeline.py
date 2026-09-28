"""
Multi-cloud Apache Beam pipeline PoC.
Same transform logic runs on GCP (Dataflow), Azure (Synapse Spark), AWS (Glue).
"""

import json
import logging
import argparse
import datetime
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition


# ---------- CLOUD-AGNOSTIC TRANSFORM ----------
class ParseAndValidate(beam.DoFn):
    """Parse JSON, validate required fields, enrich with metadata."""

    def process(self, element):
        try:
            record = json.loads(element.decode('utf-8'))

            if not record.get('customer_id'):
                logging.warning(f"Missing customer_id: {record}")
                return

            if record.get('amount', 0) <= 0:
                logging.warning(f"Invalid amount: {record}")
                return

            record['processed_at'] = datetime.datetime.utcnow().isoformat()
            yield record

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON: {e}")
            return


# ---------- BIGQUERY SCHEMA ----------
SCHEMA = {
    'fields': [
        {'name': 'customer_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'name', 'type': 'STRING', 'mode': 'NULLABLE'},
        {'name': 'amount', 'type': 'FLOAT', 'mode': 'REQUIRED'},
        {'name': 'event_time', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
        {'name': 'processed_at', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
    ]
}


# ---------- PIPELINE ----------
def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_subscription', required=True,
                        help='Pub/Sub subscription (projects/../subscriptions/..)')
    parser.add_argument('--output_table', required=True,
                        help='BigQuery table (project:dataset.table)')
    known_args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)
    options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=options) as p:
        (p
         | 'Read from Pub/Sub' >> beam.io.ReadFromPubSub(
             subscription=known_args.input_subscription,
             with_attributes=False)
         | 'Parse and Validate' >> beam.ParDo(ParseAndValidate())
         | 'Write to BigQuery' >> WriteToBigQuery(
             table=known_args.output_table,
             schema=SCHEMA,
             create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
             write_disposition=BigQueryDisposition.WRITE_APPEND,
             method='STREAMING_INSERTS')
         )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
