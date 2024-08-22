from pprint import pprint
import argparse
from prefect import flow, get_run_logger

from prefect.deployments import Deployment
from prefect.infrastructure import Process

from sous_chef import RunPipeline, recipe_loader
import statsd

statsd_url = "stats.tarbell.mediacloud.org"

prod_stats_directory = "mc.prod.system-metrics"
staging_stats_directory = "mc.staging.system-metrics"


@flow()
def RunMetrics(test=False, endpoint="", api_block="mediacloud-api-key", realm="prod"):
	logger = get_run_logger()
	stats_directory= f"mc.{realm}.system-metrics"
	statsd_client = statsd.StatsdClient(
		statsd_url, None, stats_directory)

	mixins_file = open("queries.yaml", "r")
	recipe_file = open("QueryRecipe.yaml").read()

	mixins = recipe_loader.load_mixins(mixins_file)
	if test:
		mixins = [mixins[0]]
	
	if not staging_only:
		#For Prod
		run_data = {}
		for template_params in mixins:
			template_params["API_BLOCK"]=api_block
			template_params["ENDPOINT"] = endpoint
			json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
			json_conf["name"] = template_params["NAME"]

			#run. that. pipeline!!!
			results = RunPipeline(json_conf)

			name = template_params["NAME"]
			if(len(results) > 0):
				list_elapsed = list(results.values())[0]["ElapsedTime"]
				run_data[f"list.{name}"] = list_elapsed

				count_elapsed = list(results.values())[1]["ElapsedTime"]
				run_data[f"count.{name}"] = count_elapsed

				#Actually report the data here
				logger.info(f"{name}:{list_elapsed}:{count_elapsed}")
				statsd_client.timing(f"list.{name}", list_elapsed)
				statsd_client.timing(f"count.{name}", count_elapsed)

	

@flow()
def DailyMetrics(test=False, staging_only=False):
	if not staging_only:
		RunMetrics(test)
	RunMetrics(test, endpoint='http://mcweb-staging.steinam.angwin/api/', api_block="mc-staging-test-api-key", realm="staging")

@flow()
def DevMetrics(test=False, endpoint="", api_block=""):
	RunMetrics(test, endpoint, api_block, realm="dev")




if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--test", action='store_true')
	args = parser.parse_args()
	RunMetrics(args.test)



