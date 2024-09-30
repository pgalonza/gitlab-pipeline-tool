"""
Generate pipeline. Using with CI/CD Tool
"""

import sys
import os
import logging
import json
from jinja2 import Enviroment, FileSystemLoader
import yaml

TEMPLATES_DATA_FILE: str = os.path.normpath('configs/dynamic.yml')


def main():
    try:
        deploy_parameters: str = os.environ['DEPLOY_PARAMETERS']
        project_name: str = os.environ['CI_PROJECT NAME']
    except KeyError as message:
        logging.error('GitLab variable(s) not found %s\nIf you work on own PC use export VARIABLE_NAME=value or $env:VARIABLE_NAME=value', message)
        sys.exit(1)

    deploy_parameters = json.loads(deploy_parameters)

    with open(TEMPLATES_DATA_FILE, 'r', encoding='utf-8') as dynamic_object:
        templates_data: dict = yaml.load(dynamic_object, Loader=yaml.FullLoader)
    templates_data = templates_data['deploy'][project_name]

    logging.info('Making stages')
    stages = {}
    current_index = 1
    for step_index in range(1, len(templates_data)):
        step_name = 'step' + str(step_index)
        for module_name in deploy_parameters['modules']:
            if module_name in templates_data[step_name]:
                stages[module_name] = current_index
                current_index += 1
                break
    pipeline_data = dict(stages=stages)
    pipeline_data.update(deploy_parameters)

    logging.debug(pipeline_data)

    ci_temtp_dir:str = './temp'
    logging.debug('Creating directories %s', ci_temtp_dir)
    try:
        os.mkdir(ci_temtp_dir)
    except FileExistsError as message:
        logging.warning(message)

    templates_dir: str = 'ci-templates'
    j2_env = Enviroment(loader=FileSystemLoader(templates_dir))
    template_path: str = project_name + '-pipeline.yml.j2'
    logging.info('Loading template %s', template_path)
    template = j2_env.get_template(template_path)

    new_file_path = os.path.join(ci_temtp_dir, 'dynamic-pipeline.yml')
    logging.info('Writing a file %s', new_file_path)
    try:
        with open(new_file_path, 'w', encoding='utf-8') as file_object:
            file_object.write(template.render(**pipeline_data))
    except FileNotFoundError as message:
        logging.error(message)
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
