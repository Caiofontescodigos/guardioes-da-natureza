# Guardiões da Caatinga

Jogo de batalha automática (auto-battler) por turnos desenvolvido em Python com
Pygame. Você treina animais do sertão, evolui e avança por biomas enfrentando
inimigos, chefes e grupos de elite.

## Como jogar

```bash
cd guardioes_da_caatinga
python3 main.py
```

Dependências: `pygame>=2.5.0` (ver `requirements.txt`).

## Funcionalidades

- **Batalhas automáticas** por turnos com sistema de turnos por velocidade:
  crítico, esquiva, buffs e debuffs, sangramento, veneno, escudo, contra-ataque
  e regeneração.
- **6 animais jogáveis**, cada um com uma função de equipe:
  - Tatu-bola (Tanque), Lobo-guará (Assassino), Arara-azul (Ataque a Distância),
    Tamanduá-bandeira (Controle), Capivara (Suporte) e Onça-pintada (DPS).
- **5 biomas** com dificuldade crescente: Caatinga, Cerrado, Pantanal,
  Mata Atlântica e Amazônia.
- **Mapas gerados proceduralmente** por andar, com nós de combate e **nós ELITE**
  (inimigos mais fortes com recompensas maiores).
- **Inimigos, elites e chefes** regionais com níveis escalonados.
- **Bestiário** com descobertas de animais e criaturas.
- **Como Jogar**: guia rápido com objetivo, mapa, combate, equipe e controles.
- **Acampamento**: melhorias permanentes e montagem de equipe (MELHORIAS/EQUIPE).
- **Loja do Sertão** como evento de mapa.
- **Configurações** com tela cheia/resolução, volume e mudo da música,
  velocidade do combate, opções visuais de dano/log, confirmação ao sair e
  restauração dos padrões.
- **3 slots de save** com migração automática de versões antigas (backup `.bak`).

## Sistema de evolução permanente

- Ao atingir o **nível 6**, o animal **evolui automaticamente** para a
  **Evolução 1** e recebe imediatamente:
  1. Bônus padrão de status (HP, ATK, DEF e SPD) — definidos em
     `EVOLUTION_1_BONUS`.
  2. Uma **melhoria específica da espécie** (dado permanente):
     - **Tatu-bola — Carapaça Reforçada**: +Def e redução de dano.
     - **Lobo-guará — Passos Velozes**: +Vel e chance de crítico.
     - **Arara-azul — Ataque Preciso**: +ATK e dano crítico ampliado.
     - **Tamanduá-bandeira — Defesa Natural**: +Def e +HP.
     - **Capivara — Vitalidade**: +HP e regeneração por turno.
     - **Onça-pintada — Instinto Predador**: +ATK, dano crítico ampliado e
       execução de inimigos com pouca vida.
- **Progresso permanente no Save**: evolução, bônus de status e melhoria
  específica **nunca** são perdidos ao trocar a equipe, fechar/reabrir o jogo ou
  perder uma run na jogada. Só desaparecem se o save for apagado.
- **Tela de evolução** mostra a nova forma, os status aumentados e a melhoria
  específica recebida.
- **Saves antigos são migrados automaticamente**: animais já no nível 6 (ou
  acima) recebem a evolução e a melhoria correspondente exatamente uma vez.

## Estrutura

```
guardioes_da_caatinga/
  main.py            # ponto de entrada
  config.py          # constantes de balanceamento, cores e cargas de dados
  data/              # animais, inimigos, biomas, melhorias, eventos, relíquias
  src/
    entities/        # animal, inimigo e personagem (combate)
    combat/          # sistema de batalha automático
    map/             # gerador de mapas (nós e elites)
    save/            # SaveManager (permanência) e Bestiário
    progression/     # nível/XP
    ui/              # telas, menu, layout, texto, HUD de combate
    audio/           # música e efeitos
    assets/          # gerenciamento de imagens
  saves/             # save_1.json, save_2.json, save_3.json
```

## Saves

Cada `saves/save_N.json` é totalmente independente. A separação é:

- **Permanente**: animais desbloqueados, nível, XP, evolução, bônus de evolução,
  melhoria específica, Bestiário, criaturas descobertas, biomas desbloqueados e
  estatísticas.
- **Temporário (run)**: posição no mapa, nós visitados, caminho atual e estado
  da batalha. Tudo isso é descartado ao fim da run, sem afetar o progresso
  permanente.