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
def RunMetrics(test=False, endpoint="default", api_block="mediacloud-api-key", realm="prod"):
	logger = get_run_logger()
	stats_directory= f"mc.{realm}.system-metrics"
	statsd_client = statsd.StatsdClient(
		statsd_url, None, stats_directory)

	mixins_file = open("queries.yaml", "r")
	recipe_file = open("QueryRecipe.yaml").read()

	mixins = recipe_loader.load_mixins(mixins_file)

	#If testing, only run the very first query, rather than the whole barrage. 
	if test:
		mixins = [mixins[0]]
	

	run_data = {}
	for template_params in mixins:
		template_params["API_BLOCK"] = api_block
		template_params["ENDPOINT"] = endpoint
		json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
		json_conf["name"] = template_params["NAME"]
		print(json_conf)
		#run. that. pipeline!!!
		error = False
		name = template_params["NAME"]
		try:
			results = RunPipeline(json_conf)
		except RuntimeError:
			#If one of these breaks, just move on for now. Better error catching is needed in sous-chef to catch usefully if XOR one returns 
			statsd_client.timing(f"list.{name}", 0)
			statsd_client.timing(f"count.{name}", 0)
			#statsd_client.gauge(f"error.{name}", 1)
		else:
			if(len(results) > 0 ):
				list_elapsed = list(results.values())[0]["ElapsedTime"]
				run_data[f"list.{name}"] = list_elapsed
				count_elapsed = list(results.values())[1]["ElapsedTime"]
				run_data[f"count.{name}"] = count_elapsed

				#Actually report the data here
				logger.info(f"{name}:{list_elapsed}:{count_elapsed}")
				statsd_client.timing(f"list.{name}", list_elapsed)
				statsd_client.timing(f"count.{name}", count_elapsed)
				#statsd_client.gauge(f"error.{name}", 0)

	

@flow()
def DailyMetrics(test=False, staging_only=False):
	if not staging_only:
		RunMetrics(test)
	RunMetrics(test, 
		
		endpoint='https://mcweb-staging.tarbell.mediacloud.org/api/', 
		api_block="mc-staging-test-api-key", 
		realm="staging")

@flow()
def DevMetrics(test=False, endpoint="default", api_block="mediacloud-api-key"):
	RunMetrics(test, endpoint, api_block, realm="dev")




if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--test", action='store_true')
	args = parser.parse_args()
	DailyMetrics(args.test)



