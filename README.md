# Check boxes and buttons for GitLab

This solution will help you add controls (checkbox, drop-down list, etc.) similar to Jenkins.

The implementation includes a desktop utility that generates a request in the GitLab api and puts  information about selected elements in json format in to GitLab variable. Data from json parsed by a python script, then a future pipeline downstream pipeline is created from the Jinja2 template.

![How to work](/assets/diagram.png)

![CI/CD Tool](/assets/cicd-tool.png)
