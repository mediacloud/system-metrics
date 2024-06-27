from pprint import pprint
import argparse
from prefect import flow, get_run_logger
from prefect.runtime import flow_run
from sous_chef import RunPipeline, recipe_loader


def RunMetrics():
	mixins_file = open("queries.yaml").read()
	recipe_file = open("QueryRecipe.yaml").read()

	mixins = recipe_loader.load_mixins(mixins_file)

	run_data = {}
	for template_params in mixins:
		json_conf = recipe_loader.t_yaml_to_conf(recipe_file, **template_params)
		print(json_conf)
		run_data_ = RunPipeline(json_conf)
		print(run_data_)



if __name__ == "__main__":
	RunMetrics()

