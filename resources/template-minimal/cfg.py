env = None # could be 'dev' or 'prod'
do_preprocess = True

# Auto code invalidation (oryxflow >= 26.7.12) is ON: editing task/helper code
# reruns the affected band automatically. Conscious knobs, uncomment to change:
# import oryxflow
# oryxflow.settings.code_version_auto = False        # explicit code_version only
# oryxflow.settings.code_version_auto_expensive_s = 600  # tasks slower than this
#                                                    # warn instead of auto-rerunning

import datetime
dt_start = datetime.date(2010,1,1)
dt_end = datetime.date(2020,1,1)

# load protected credentials
try:
    import yaml
    with open('.creds.yaml') as fh:
        cfg_yaml = yaml.safe_load(fh)
except:
    pass
