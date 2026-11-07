"""Build a game-specific profile using only resources already on disk."""
import json
from app.pokedex_catalog import PACKAGES, GAME_PACKAGES, STAT_LABELS, TYPE_NAMES

METHODS = {'level-up':'Por nivel', 'machine':'MT / MO', 'tutor':'Tutor de movimientos', 'egg':'Por crianza',
           'stadium-surfing-pikachu':'Evento de Pokémon Stadium', 'light-ball-egg':'Crianza con Bola Luminosa',
           'form-change':'Cambio de forma'}
EGG_GROUPS = {'monster':'Monstruo','water1':'Agua 1','bug':'Bicho','flying':'Volador','ground':'Campo',
              'fairy':'Hada','plant':'Planta','humanshape':'Humanoide','water3':'Agua 3','mineral':'Mineral',
              'indeterminate':'Amorfo','water2':'Agua 2','ditto':'Ditto','dragon':'Dragón','no-eggs':'Sin crianza'}
GROWTH = {'slow':'Lento','medium':'Medio','fast':'Rápido','medium-slow':'Medio lento',
          'slow-then-very-fast':'Errático','fast-then-very-slow':'Fluctuante'}
HABITATS = {'cave':'Cueva','forest':'Bosque','grassland':'Pradera','mountain':'Montaña','rare':'Poco habitual',
            'rough-terrain':'Terreno accidentado','sea':'Mar','urban':'Urbano','waters-edge':'Orilla del agua'}
COLORS = {'black':'Negro','blue':'Azul','brown':'Marrón','gray':'Gris','green':'Verde','pink':'Rosa',
          'purple':'Morado','red':'Rojo','white':'Blanco','yellow':'Amarillo'}
SHAPES = {'ball':'Redondeado','squiggle':'Serpentino','fish':'Pisciforme','arms':'Con brazos',
          'blob':'Amorfo','upright':'Erguido','legs':'Bípedo','quadruped':'Cuadrúpedo','wings':'Alado',
          'tentacles':'Con tentáculos','heads':'Varias cabezas','humanoid':'Humanoide','bug-wings':'Alas de insecto','armor':'Con caparazón'}


def generation_id(resource):
    return int(resource['url'].rstrip('/').rsplit('/',1)[-1])


def cached(directory, endpoint, resource):
    if not resource:
        return {}
    names = [resource['name']]
    if resource.get('url'):
        names.append(resource['url'].rstrip('/').rsplit('/',1)[-1])
    for name in names:
        try:
            return json.loads((directory / 'cache' / endpoint / f'{name}.json').read_text())
        except (OSError, ValueError):
            continue
    return {}


def resource_name(directory, endpoint, resource):
    info = cached(directory, endpoint, resource)
    names = info.get('names', [])
    for language in ('es','en'):
        found = next((item['name'] for item in names if item['language']['name'] == language), None)
        if found:
            return found
    return resource['name'].replace('-', ' ').title()


def historical_values(current, past_records, generation, field, key):
    """Apply partial changes by slot/stat, including explicit removals."""
    values = {key(item):item for item in current}
    for past in sorted(past_records, key=lambda item:generation_id(item['generation']), reverse=True):
        if generation <= generation_id(past['generation']):
            values.update({key(item):item for item in past[field]})
    return values


def defenses(directory, types, generation):
    relations = []
    for kind in types:
        data = cached(directory,'type', {'name':kind['slug']})
        if not data:
            return []
        relation = data['damage_relations']
        for past in sorted(data.get('past_damage_relations', []), key=lambda item:generation_id(item['generation'])):
            if generation <= generation_id(past['generation']):
                relation = past['damage_relations']
                break
        relations.append(relation)
    if not relations:
        return []
    groups = {'Debilidades':[], 'Resistencias':[], 'Inmunidades':[]}
    for slug, label in TYPE_NAMES.items():
        introduced = 6 if slug == 'fairy' else 2 if slug in {'dark','steel'} else 1
        if introduced > generation:
            continue
        factor = 1
        for relation in relations:
            for field, multiplier in [('no_damage_from',0),('half_damage_from',0.5),('double_damage_from',2)]:
                if any(item['name'] == slug for item in relation[field]):
                    factor *= multiplier
        if factor == 1:
            continue
        group = 'Inmunidades' if factor == 0 else 'Debilidades' if factor > 1 else 'Resistencias'
        groups[group].append({'slug':slug,'name':label,'factor':{0:'×0',0.25:'×¼',0.5:'×½',2:'×2',4:'×4'}[factor]})
    return [{'label':label,'types':items} for label,items in groups.items() if items]


def build_profile(directory, selected, edition, all_pokemon):
    pokemon = cached(directory,'pokemon', {'name':str(selected['pokemon_id'])})
    species = cached(directory,'pokemon-species', {'name':str(selected['id'])})
    if not pokemon or not species:
        return None
    generation = edition['generation']
    package = PACKAGES[GAME_PACKAGES[edition['game_id']]]
    group = package['version_groups'][edition['game_id']]
    moves = {}
    for item in pokemon.get('moves', []):
        for detail in item['version_group_details']:
            if detail['version_group']['name'] != group:
                continue
            method = detail['move_learn_method']['name']
            move = {'name':resource_name(directory,'move',item['move']), 'level':detail['level_learned_at']}
            if move not in moves.setdefault(method, []):
                moves[method].append(move)
    move_groups = []
    for method in list(METHODS) + sorted(set(moves) - set(METHODS)):
        if method in moves:
            move_groups.append({'key':method,'name':METHODS.get(method, method.replace('-',' ').capitalize()),
                                'moves':sorted(moves[method], key=lambda item:(item['level'],item['name']))})
    general_abilities = [{'name':resource_name(directory,'ability',item['ability']), 'hidden':item['is_hidden']} for item in pokemon.get('abilities', []) if item['ability']]
    general_effort = [{'name':STAT_LABELS[item['stat']['name']],'value':item['effort']} for item in pokemon.get('stats', []) if item['effort'] and item['stat']['name'] in STAT_LABELS]
    general_types = [{'slug':item['type']['name'],'name':TYPE_NAMES.get(item['type']['name'],item['type']['name'])} for item in pokemon.get('types', [])]
    abilities = []
    if generation >= 3:
        slots = historical_values(pokemon.get('abilities', []), pokemon.get('past_abilities', []),generation,'abilities',lambda item:item['slot'])
        for slot, item in sorted(slots.items()):
            if item['ability'] and (generation >= 5 or not item['is_hidden']):
                abilities.append({'name':resource_name(directory,'ability',item['ability']), 'hidden':item['is_hidden']})
    effort = []
    if generation >= 3 and 'past_stats' in pokemon:
        values = historical_values(pokemon['stats'],pokemon['past_stats'],generation,'stats',lambda item:item['stat']['name'])
        effort = [{'name':STAT_LABELS[slug],'value':item['effort']} for slug,item in values.items() if item['effort'] and slug in STAT_LABELS]
    held_items = []
    if generation >= 2:
        for item in pokemon.get('held_items', []):
            for detail in item['version_details']:
                if detail['version']['name'] == edition['version']:
                    held_items.append({'name':resource_name(directory,'item',item['item']), 'rarity':detail['rarity']})
    gender = species.get('gender_rate')
    gender_label = 'Sin sexo' if gender == -1 else f'{100-gender*12.5:g}% ♂ · {gender*12.5:g}% ♀' if gender is not None else None
    # Follow only species in this Pokédex: later babies and evolutions stay out.
    by_id = {item['id']:item for item in all_pokemon}
    root = by_id[selected['id']]
    visited = {root['id']}
    while root['evolves_from'] in by_id and root['evolves_from'] not in visited:
        root = by_id[root['evolves_from']]
        visited.add(root['id'])
    stages, stage, visited = [], [root], set()
    while stage:
        stages.append(stage)
        visited.update(item['id'] for item in stage)
        parent_ids = {item['id'] for item in stage}
        stage = [item for item in all_pokemon if item['evolves_from'] in parent_ids and item['id'] not in visited]
    names = [{'language':item['language']['name'],'name':item['name']} for item in species['names']]
    habitat = (species.get('habitat') or {}).get('name')
    shape = (species.get('shape') or {}).get('name')
    color = (species.get('color') or {}).get('name')
    category = 'Singular' if species.get('is_mythical') else 'Legendario' if species.get('is_legendary') else 'Bebé' if species.get('is_baby') else None
    growth = species['growth_rate']['name']
    pokedex_numbers = [{'name':resource_name(directory,'pokedex',item['pokedex']), 'number':item['entry_number']} for item in species.get('pokedex_numbers', [])]
    varieties = [{'name':resource_name(directory,'pokemon',item['pokemon']),'default':item['is_default']} for item in species.get('varieties', [])]
    return {'general_abilities':general_abilities,'general_effort':general_effort,'general_types':general_types,'varieties':varieties,
            'pokedex_numbers':pokedex_numbers,'gender_differences':species.get('has_gender_differences'),
            'moves':move_groups,'abilities':abilities,'effort':effort,'held_items':held_items,
            'defenses':defenses(directory,selected['types'],generation),
            'capture_rate':species.get('capture_rate'),'growth':GROWTH.get(growth,growth),
            'egg_groups':[EGG_GROUPS.get(item['name'],item['name']) for item in species.get('egg_groups', [])],
            'gender':gender_label,'egg_cycles':species.get('hatch_counter'),
            'category':category,'introduced':generation_id(species['generation']),
            'habitat':HABITATS.get(habitat,habitat),'color':COLORS.get(color,color),'shape':SHAPES.get(shape,shape),
            'evolution_stages':stages if len(visited) > 1 else [],'names':names,
            'base_experience':pokemon.get('base_experience'),'base_friendship':species.get('base_happiness')}
