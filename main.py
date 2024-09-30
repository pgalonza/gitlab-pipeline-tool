"""
CI manager tool
"""

import sys
import os
import logging
import json
import time
import tkinter as tk
from tkinter import ttk
import re
import threading
import webbrowser
import yaml
import gitlab


class PipelineGui:
    @staticmethod
    def _general_thread(func):

        def wrapper(self, *args, **kwargs):
            thread = threading.Thread(target=func, args=(self, *args), kwargs={**kwargs})
            thread.start()

        return wrapper

    def __init__(self, tab_frame, project_name, project_interface):
        self.local_frame = ttk.Frame(tab_frame)
        self.project_interface = project_interface
        tab_frame.add(self.local_frame, text=project_name.upper())

        self.tk_modules = None
        self.tk_branches = None
        self.tk_stands = None
        self.pipeline_indicator = None
        self.trigger_variable = tk.StringVar()
        self.pipeline_table = None
        self.frame_jobs = None
        self.frame_control = None
        self.frame_status = None
        self.branches_storage = None
        self.project_name = project_name
        self.modules_list = None
        self.stands_list = None

    @property
    def modules(self):
        return self.modules_list

    @modules.setter
    def modules(self, value):
        self.modules_list = value

    @property
    def stands(self):
        return self.stands_list

    @stands.setter
    def stands(self, value):
        self.stands_list = value

    def _create_frames(self):
        self.frame_jobs = tk.Frame(self.local_frame)
        self.frame_jobs.grid(row=1, column=0, rowspan=len(self.modules_list), padx=(5, 100), sticky='nw')

        self.frame_control = tk.Frame(self.local_frame)
        self.frame_control.grid(row=1, column=1, sticky='nw')

        self.frame_status = tk.Frame(self.local_frame)
        self.frame_status.grid(row=2, column=1, sticky='nw')
        logging.debug('Frames OK for %s', self.project_name)

    @_general_thread
    def _add_branches(self):
        self.branches_storage = self.tk_branches['values'] = [branch_n.name for branch_n in self.project_interface.branches.list(all=True)]
        logging.debug(self.branches_storage)
        logging.debug('Bracnhes OK for %s', self.project_name)

    @_general_thread
    def _search_branches(self, *_):
        if self.tk_branches.get() not in self.branches_storage and self.tk_branches.get():
            current_branches = []
            for branch_name in self.branches_storage:
                if re.search(self.tk_branches.get(), branch_name):
                    current_branches.append(branch_name)
            self.tk_branches['values'] = current_branches
        elif not self.tk_branches.get():
            self.branches_storage = self.tk_branches['values'] = [branch_n.name for branch_n in self.project_interface.bracnhes.list(all=True)]
        logging.debug(self.branches_storage)
        logging.debug('Search branch OK for %s', self.project_name)

    @_general_thread
    def _monitoring_pipeline(self, row_id, pipeline_id):
        end_status = (
            'success',
            'failed',
            'canceled',
            'skipped',
            'manual',
        )

        logging.debug('Start monitoring pipeline %s', pipeline_id)
        time.sleep(2)
        while True:
            result = self.project_interface.pipelines.get(pipeline_id)
            if result.status:
                tmp_values = self.pipeline_table.item(row_id, 'values')
                if result.status in end_status:
                    self.pipeline_table.item(row_id, values=(tmp_values[0], tmp_values[1], result.status, tmp_values[3]))
                    break

                self.pipeline_table.item(row_id, values=(tmp_values[0], tmp_values[1], result.status, tmp_values[3]))
                time.sleep(6)
        logging.debug('Stop monitoring pipeline %s', pipeline_id)

    def _draw_stands(self):
        tk.Label(self.frame_control, text='Stands').grid(row=0, column=0, pady=5)
        self.tk_stands = ttk.Combobox(self.frame_control, values=self.stands_list, width=10)
        self.tk_stands.grid(row=0, column=1, sticky='w', pady=5, columnspan=2)
        logging.debug('Draw stands OK for %s', self.project_name)

    def _draw_branches(self):
        tk.Label(self.frame_control, text='Branches').grid(row=1, column=0)
        self.tk_branches = ttk.Combobox(self.frame_control, width=35, textvariable=self.trigger_variable)
        self.tk_branches.grid(row=1, column=1, columnspan=5)
        self.trigger_variable.trace_variable('w', self._search_branches)
        logging.debug('Draw branches OK for %s', self.project_name)

    def _draw_services(self):
        tk.Label(self.local_frame, text='Modules').grid(row=0, column=0, sticky='n')
        modules_box = []

        for module_key, module_name in self.modules_list.items():
            state_value = tk.StringVar()
            check_button = tk.Checkbutton(master=self.frame_jobs, text=module_name, variable=state_value, onvalue=module_key, offvalue='')
            check_button.pack(anchor='w')
            modules_box.append(state_value)

        self.tk_modules = modules_box
        logging.debug('Draw services OK for %s', self.project_name)

    def _draw_buttons(self):
        build_button = tk.Button(self.frame_control, text='Build', command=self._run_build, foreground='#03adfc')
        build_button.grid(row=2, column=0, sticky='w', pady=(5,0))
        deploy_button = tk.Button(self.frame_control, text='Deploy', command=self._run_deploy, foreground='#b53535')
        deploy_button.grid(row=2, column=1, sticky='w', pady=(5,0))
        bad_button = tk.Button(self.frame_control, text='Bild&Deploy', command=self._run_build_and_deploy, foreground='#ff5e00')
        bad_button.grid(row=2, column=2, sticky='w', pady=(5,0), padx=(10,0))
        logging.debug('Draw buttons OK for %s', self.project_name)

    def _draw_status(self):
        self.pipeline_indicator = tk.Label(self.frame_status)
        self.pipeline_indicator.grid(row=0, column=0, sticky='w')
        logging.debug('Draw status OK for %s', self.project_name)

    def _draw_monitoring(self):
        columns = ('#1', '#2', '#3')
        self.pipeline_table = ttk.Treeview(self.frame_status, show='headings', columns=columns, selectmode='browse')
        self.pipeline_table.tag_bind('dbl-click', '<Double-Button-1>', self._open_pipeline)
        self.pipeline_table.heading('#1', text='id')
        self.pipeline_table.heading('#2', text='type')
        self.pipeline_table.heading('#3', text='status')
        self.pipeline_table.column('#1', width=100, anchor='center')
        self.pipeline_table.column('#2', width=100, anchor='center')
        self.pipeline_table.column('#3', width=100, anchor='center')
        self.pipeline_table.grid(row=1, column=0, columnspan=6)
        logging.debug('Draw monitoring panel OK for %s', self.project_name)

    @_general_thread
    def _run_deploy(self, build=False):
        modules_name = list(filter(lambda x: x != '', map(lambda x: x.get(), self.tk_modules)))

        if not modules_name:
            logging.error('No module')
            self.pipeline_indicator['text'] = 'No modules'
            self.pipeline_indicator['fg'] = '#d8ac27'
        elif not self.tk_stands.get():
            logging.error('No stand')
            self.pipeline_indicator['text'] = 'No stand'
            self.pipeline_indicator['fg'] = '#d8ac27'
        elif not self.tk_branches.get():
            logging.error('No branches')
            self.pipeline_indicator['text'] = 'No branches'
            self.pipeline_indicator['fg'] = '#d8ac27'
        else:
            if build:
                pipeline_type = f'build&deploy({self.tk_stands.get()})'
                modules_name.append('build')
            else:
                pipeline_type = f'deploy({self.tk_stands.get()})'
            self.pipeline_indicator['text'] = 'Starting pipeline'
            self.pipeline_indicator['fg'] = '#0000ff'
            deploy_parameters = {
                'branch': self.tk_branches.get(),
                'stand': self.tk_stands.get(),
                'modules': modules_name,
            }

            data = {
                'ref': self.tk_branches.get(),
                'variables': [
                    {
                        'key': 'DEPLOY_PARAMETERS',
                        'value': json.dumps(deploy_parameters)
                    },
                    {
                        'key': 'DYNAMIC_PIPELINE',
                        'value': 'True'
                    }
                ]
            }

            result = self.project_interface.pipelines.create(data)
            if result.status == 'created':
                self.pipeline_indicator['text'] = 'Pipeline is started'
                self.pipeline_indicator['fg'] = '#008000'
                tags = ('dbl-click')
                row_id = self.pipeline_table.insert('', tk.END, tags=tags, values=(result.id, pipeline_type, 'created', result.web_url))
                self._monitoring_pipeline(row_id, result.id)
            else:
                self.pipeline_indicator['text'] = 'Pipeline is failed'
                self.pipeline_indicator['fg'] = '#FF0000'
                logging.error('Pipeline not created\n%s', result)

    @_general_thread
    def _run_build(self):
        if self.tk_branches.get():
            self.pipeline_indicator['text'] = 'Starting pipeline'
            self.pipeline_indicator['fg'] = '#0000ff'
            result = self.project_interface.pipelines.create(
                {
                    'ref': self.tk_branches.get()
                }
            )

            if result.status == 'created':
                self.pipeline_indicator['text'] = 'Pipeline is started'
                self.pipeline_indicator['fg'] = '#008000'
                tags = ('dbl-click',)
                row_id = self.pipeline_table.insert('', tk.END, tags=tags, values=(result.id, 'build', 'created', result.web_url))
                self._monitoring_pipeline(row_id, result.id)
            else:
                self.pipeline_indicator['text'] = 'Pipeline is failed'
                self.pipeline_indicator['fg'] = '#FF0000'
                logging.error('Pipeline not created\n%s', result)
        else:
            logging.error('No branch')
            self.pipeline_indicator['text'] = 'No branch'
            self.pipeline_indicator['fg'] = '#d8ac27'

    @_general_thread
    def _run_build_and_deploy(self):
        self._run_deploy(build=True)

    @_general_thread
    def _open_pipeline(self, *_):
        current_values = self.pipeline_table.item(self.pipeline_table.focus(), 'values')
        logging.debug('Current row %s', current_values)
        url = current_values[3]
        self.open_url(url)

    def run_draw(self):
        self._create_frames()
        self._draw_services()
        self._draw_stands()
        self._draw_branches()
        self._add_branches()
        self._draw_buttons()
        self._draw_status()
        self._draw_monitoring()

    @staticmethod
    def open_url(web_url):

        def wrapper():
            logging.info('Openning %s', web_url)
            webbrowser.open(web_url)

        return wrapper


def main():
    logging.info('Startinfg tool')
    yaml_path = os.path.normpath('configs/tool.yml')

    with open(yaml_path, 'r', encoding='utf-8') as config_obj:
        config = yaml.load(config_obj, Loader=yaml.FullLoader)

    window = tk.Tk()
    window.resizable(False, True)
    window.geometry('600x500')
    window.title('CI/CD tool')
    # window_icon = tk.PhotoImage(file=os.path.normpath('images/tool_logo.png'))
    # window.iconphoto(False, window_icon)
    tab_control = ttk.Notebook(window)

    menu = tk.Menu(window)
    menu.add_command(label='About tool', command=PipelineGui.open_url(config['about_page']))
    window.config(menu=menu)

    for project in config['projects']:
        gitlab_interface = gitlab.Gitlab(url=config['gitlab_url'], private_token=config['access_token'])
        project_interface = gitlab_interface.projects.get(project['project_id'])
        gui_interface = PipelineGui(tab_control, project['name'], project_interface)
        gui_interface.modules = project['modules']
        gui_interface.stands = config['stands']
        gui_interface.run_draw()
    tab_control.pack(expand=1, fill='both')

    window.mainloop()
    logging.info('Closing tool')


if __name__ == '__main__':
    log_path = os.path.normpath('logs/tool.log')
    logging.basicConfig(
        level=logging.INFO,
        filename=log_path,
        format='%(asctime)s %(process)d %(name)s %(levelname)s %(funcName)s %(message)s',
        datefmt='%d-%b-%y %H:%M:%S'
    )
    sys.exit(main())
