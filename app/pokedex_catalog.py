"""Pokédex membership is shared; edition packages add historical and visual data."""
PACKAGES = {
    'kanto-gen1': {
        'pokedex':'kanto', 'generation':1, 'sprite_generation':'generation-i',
        'games':{'red':'red', 'blue':'blue', 'yellow':'yellow'},
        'version_groups':{'red':'red-blue', 'blue':'red-blue', 'yellow':'yellow'},
        'sprites':{'red':'red-blue', 'blue':'red-blue', 'yellow':'yellow'},
    },
    'kalos-gen6': {
        'pokedex':'kalos-central', 'pokedexes':('kalos-central','kalos-coastal','kalos-mountain'),
        'generation':6, 'sprite_generation':'generation-vi',
        'games':{'x':'x', 'y':'y'},
        'version_groups':{'x':'x-y', 'y':'x-y'},
        'sprites':{'x':'x-y', 'y':'x-y'},
    },
    'kanto-gen3': {
        'pokedex':'kanto', 'generation':3, 'sprite_generation':'generation-iii',
        'games':{'firered':'firered', 'leafgreen':'leafgreen'},
        'version_groups':{'firered':'firered-leafgreen', 'leafgreen':'firered-leafgreen'},
        'sprites':{'firered':'firered-leafgreen', 'leafgreen':'firered-leafgreen'},
    },
}
GAME_PACKAGES = {game:key for key, package in PACKAGES.items() for game in package['games']}
TYPE_NAMES = dict(zip(
    ('normal','fire','water','electric','grass','ice','fighting','poison','ground','flying','psychic','bug','rock','ghost','dragon','dark','steel','fairy'),
    ('Normal','Fuego','Agua','Eléctrico','Planta','Hielo','Lucha','Veneno','Tierra','Volador','Psíquico','Bicho','Roca','Fantasma','Dragón','Siniestro','Acero','Hada')))


def historical_types(pokemon, generation):
    for past in sorted(pokemon.get('past_types', []), key=lambda item:int(item['generation']['url'].rstrip('/').rsplit('/',1)[-1])):
        if generation <= int(past['generation']['url'].rstrip('/').rsplit('/',1)[-1]):
            return past['types']
    return pokemon['types']

STAT_LABELS = {
    'hp':'PS', 'attack':'Ataque', 'defense':'Defensa',
    'special':'Especial', 'special-attack':'Ataque Especial',
    'special-defense':'Defensa Especial', 'speed':'Velocidad',
}


def historical_stats(pokemon, generation):
    """Past records are partial overrides, valid up to their stated generation."""
    if 'past_stats' not in pokemon:
        return []  # An older cache cannot establish historical values reliably.
    values = {item['stat']['name']:item['base_stat'] for item in pokemon.get('stats', [])}
    for past in sorted(pokemon['past_stats'], key=lambda item:int(item['generation']['url'].rstrip('/').rsplit('/',1)[-1]), reverse=True):
        if generation <= int(past['generation']['url'].rstrip('/').rsplit('/',1)[-1]):
            values.update({item['stat']['name']:item['base_stat'] for item in past['stats']})
    order = ('hp','attack','defense','special','speed') if generation == 1 else ('hp','attack','defense','special-attack','special-defense','speed')
    if any(slug not in values for slug in order):
        return []
    return [{'slug':slug,'label':STAT_LABELS[slug],'value':values[slug]} for slug in order]
