'''DAG definition as data plus validation.

Nodes run in fixed order: ingest, features, train, evaluate,
register, deploy. Each node names its entry point, dependencies,
retry policy and per-node timeout. Schedules and sensors are data
too, so the same graph can be rendered for other orchestrators.
'''

NODE_ORDER = ['ingest', 'features', 'train', 'evaluate', 'register', 'deploy']

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = [30, 60, 120]

NODES = {
    'ingest': {
        'name': 'ingest',
        'depends_on': [],
        'entry_point': 'mlops/ingest/run.py',
        'args': [],
        'retries': 3,
        'backoff_seconds': [30, 60, 120],
        'timeout_seconds': 1800,
        'description': 'Load synthetic listings into the bronze layer.',
    },
    'features': {
        'name': 'features',
        'depends_on': ['ingest'],
        'entry_point': 'mlops/features/build.py',
        'args': [],
        'retries': 3,
        'backoff_seconds': [30, 60, 120],
        'timeout_seconds': 1200,
        'description': 'Build features from bronze data into the feature store.',
    },
    'train': {
        'name': 'train',
        'depends_on': ['features'],
        'entry_point': 'mlops/training/train.py',
        'args': [],
        'retries': 3,
        'backoff_seconds': [30, 60, 120],
        'timeout_seconds': 3600,
        'description': 'Train the salary model on current features.',
    },
    'evaluate': {
        'name': 'evaluate',
        'depends_on': ['train'],
        'entry_point': 'mlops/training/train.py',
        'args': ['--evaluate'],
        'retries': 3,
        'backoff_seconds': [30, 60, 120],
        'timeout_seconds': 1200,
        'description': 'Evaluate the trained model and record metrics.',
    },
    'register': {
        'name': 'register',
        'depends_on': ['evaluate'],
        'entry_point': 'mlops/registry/registry.py',
        'args': [],
        'retries': 3,
        'backoff_seconds': [30, 60, 120],
        'timeout_seconds': 600,
        'description': 'Register the evaluated model version in the registry.',
    },
    'deploy': {
        'name': 'deploy',
        'depends_on': ['register'],
        'entry_point': 'mlops/serving/app.py',
        'args': ['--check'],
        'retries': 3,
        'backoff_seconds': [30, 60, 120],
        'timeout_seconds': 900,
        'description': 'Verify the serving app can load the registered model.',
    },
}

SCHEDULES = [
    {
        'name': 'daily_ingest',
        'cron': '0 2 * * *',
        'timezone': 'Asia/Ho_Chi_Minh',
        'nodes': ['ingest'],
        'description': 'Daily 02:00 ingest of new bronze data.',
    },
    {
        'name': 'weekly_retrain',
        'cron': '0 2 * * 0',
        'timezone': 'Asia/Ho_Chi_Minh',
        'nodes': ['ingest', 'features', 'train', 'evaluate', 'register', 'deploy'],
        'description': 'Weekly full retrain: every node in order.',
    },
]

SENSORS = [
    {
        'name': 'new_bronze_data',
        'kind': 'sensor',
        'watches': 'bronze layer',
        'action': 'start ingest when new bronze data arrives',
        'description': 'Triggers ingest when files appear that were not seen before.',
    },
    {
        'name': 'drift_alert',
        'kind': 'sensor',
        'watches': 'drift alerts',
        'action': 'start retrain when a drift alert fires',
        'threshold_psi': 0.2,
        'threshold_ks': 0.15,
        'description': 'Triggers retrain when PSI is over 0.2 or KS is over 0.15.',
    },
]

DRIFT_PSI_THRESHOLD = 0.2
DRIFT_KS_THRESHOLD = 0.15


def get_nodes():
    return [dict(NODES[name]) for name in NODE_ORDER]


def get_node(name):
    if name not in NODES:
        raise ValueError('unknown node: ' + name)
    return dict(NODES[name])


def get_schedules():
    return [dict(item) for item in SCHEDULES]


def get_sensors():
    return [dict(item) for item in SENSORS]


def topological_order(nodes=None):
    if nodes is None:
        nodes = NODES
    names = list(nodes.keys())
    for name in names:
        for dep in nodes[name].get('depends_on', []):
            if dep not in nodes:
                raise ValueError('node ' + name + ' depends on unknown node ' + dep)
            if dep == name:
                raise ValueError('node ' + name + ' depends on itself')
    order = []
    done = set()
    remaining = list(names)
    while remaining:
        ready = [n for n in remaining if all(d in done for d in nodes[n].get('depends_on', []))]
        if not ready:
            raise ValueError('cycle detected among nodes: ' + ', '.join(sorted(remaining)))
        # Keep the declared order where several nodes are ready.
        ready.sort(key=lambda n: NODE_ORDER.index(n) if n in NODE_ORDER else len(NODE_ORDER))
        picked = ready[0]
        order.append(picked)
        done.add(picked)
        remaining.remove(picked)
    return order


def validate_dag(nodes=None):
    if nodes is None:
        nodes = NODES
    order = topological_order(nodes)
    if set(nodes.keys()) != set(NODE_ORDER) and nodes is NODES:
        raise ValueError('DAG must contain exactly the declared nodes')
    if nodes is NODES and order != NODE_ORDER:
        raise ValueError('topological order must be fixed: ' + ', '.join(NODE_ORDER))
    for name in order:
        node = nodes[name]
        if node.get('retries', 0) < 0:
            raise ValueError('node ' + name + ' has negative retries')
        if node.get('timeout_seconds', 0) <= 0:
            raise ValueError('node ' + name + ' needs a positive timeout')
        if not node.get('entry_point'):
            raise ValueError('node ' + name + ' needs an entry point')
    return order


def new_data_available(known_files, current_files):
    known = set(known_files or [])
    current = list(current_files or [])
    return sorted([path for path in current if path not in known])


def drift_alert_triggered(psi, ks):
    return float(psi) > DRIFT_PSI_THRESHOLD or float(ks) > DRIFT_KS_THRESHOLD


def sensor_should_trigger(sensor_name, payload=None):
    payload = payload or {}
    if sensor_name == 'new_bronze_data':
        new_files = new_data_available(payload.get('known_files'), payload.get('current_files'))
        return len(new_files) > 0
    if sensor_name == 'drift_alert':
        return drift_alert_triggered(payload.get('psi', 0.0), payload.get('ks', 0.0))
    raise ValueError('unknown sensor: ' + sensor_name)
