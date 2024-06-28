from pprint import pprint
import argparse
from prefect import flow, get_run_logger
from prefect.runtime import flow_run
from sous_chef import RunPipeline, recipe_loader

@flow()
def RunMetrics():
	mixins_file = open("queries.yaml", "r")
	recipe_file = open("QueryRecipe.yaml").read()

	mixins = recipe_loader.load_mixins(mixins_file)
	
	run_data = {}
	for template_params in mixins:
		json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
		json_conf["name"] = template_params["NAME"]

		results = RunPipeline(json_conf)
		
		run_data[template_params["NAME"]] = list(results.values())
	
	print(run_data)

if __name__ == "__main__":
	RunMetrics()

