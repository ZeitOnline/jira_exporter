from setuptools import setup, find_packages


setup(
    name='jira_exporter',
    version='1.0.0',
    author='Wolfgang Schnerring',
    author_email='wolfgang.schnerring@zeit.de',
    url='https://github.com/ZeitOnline/jira_exporter',
    description='',
    long_description=(
        open('README.rst').read() +
        '\n\n' +
        open('CHANGES.txt').read()),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='BSD',
    install_requires=[
        'jira',
        'prometheus_client',
        'setuptools',
    ],
    entry_points={'console_scripts': [
        'jira_exporter = jira_exporter:main',
    ]}
)
