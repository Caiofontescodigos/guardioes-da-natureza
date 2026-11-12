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

## Fluxo de navegação

1. **Menu principal**: JOGAR, SOBRE, CONFIGURAÇÕES e SAIR.
2. **JOGAR** abre a seleção dos três slots de save.
3. Ao selecionar ou criar um slot, abre o **menu da partida** daquele save.
4. O menu da partida reúne Bestiário, Acampamento, Conquistas,
   Configurações, Sobre e **JOGAR**, que abre a seleção de equipe.
5. Confirmar a equipe inicia ou retoma a jornada; voltar durante a jornada
   retorna ao menu da partida, com o progresso salvo.
6. O botão **SELECIONAR SAVE** no menu da partida retorna à seleção de slots.
7. O **SAIR** do menu da partida encerra apenas a sessão do slot atual:
   salva o progresso, desvincula o save ativo e volta à seleção de slots sem
   apagar dados e sem fechar o jogo. O **SAIR** do menu principal continua
   encerrando o aplicativo.
8. Se toda a equipe for derrotada, a tentativa atual termina e a tela de
   **GAME OVER** usa a arte original `TelaGameOver.png` em um painel menor,
   sobre o fundo da região (bioma ou fase do chefe) onde a equipe caiu. A
   equipe é recuperada (25% do HP máximo, mínimo 1) e o jogador escolhe entre:
   - **TENTAR NOVAMENTE** (`Enter`/`Espaço` ou clique): inicia uma nova
     tentativa desde o primeiro mapa (Caatinga);
   - **VOLTAR AO MENU** (`Esc` ou clique): retorna ao menu interno do save
     ativo. Ao iniciar a próxima partida por esse menu, a jornada também
     recomeça no primeiro mapa (Caatinga).
   Em ambos os casos o save atual é preservado (animais desbloqueados,
   bestiário, ouro, estatísticas, configurações e demais dados permanentes) e
   apenas o estado temporário da tentativa (mapa, batalha e eventos) é
   descartado. Nenhum slot é apagado ou criado.

O slot ativo é mantido pelo `SaveManager`; todas as telas da partida
(Bestiário, Conquistas, equipe, ouro, estatísticas e jornada) usam os
dados desse mesmo slot, sem armazenamento paralelo. Os sistemas de Inventário
e Missões continuam disponíveis no código e em suas telas de origem, mas não
são mais expostos pelo menu da partida.

## Funcionalidades

- **Batalhas automáticas** por turnos com sistema de turnos por velocidade:
  crítico, esquiva, buffs e debuffs, sangramento, veneno, escudo, contra-ataque
  e regeneração. Pressione `Enter` para pular a batalha direto para o resultado.
- **Tela de Game Over** em painel compacto sobre o fundo da região onde a
  equipe foi derrotada, com estatísticas do save, equipe, tentativa rápida no
  primeiro mapa e retorno ao menu do save.
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
- **Armazém do Seu Zé** como evento de mapa: as quatro cartas da arte são
  botões de compra por clique direto — Cruz Dourada (1000), Poção de Ataque
  (25), Poção de Defesa (25) e Poção de Cura (20). O ouro e as mensagens de
  compra aparecem sobre a própria arte da loja.
- **Configurações** com tela cheia/resolução, volume e mudo da música,
  velocidade do combate, opções visuais de dano/log, confirmação ao sair e
  restauração dos padrões.
- **3 slots de save** com migração automática de versões antigas (backup `.bak`).

## Animais caídos

- Um animal que chega a 0 HP fica **caído** e permanece assim após a vitória.
- Para reanimar, use a **Cruz Dourada** no Inventário (todos os caídos voltam
  com 50% do HP máximo) ou passe pelo **Acampamento**.
- O indicador **CAÍDO** aparece na seleção de equipe e no Inventário.
- A **derrota total** da equipe continua encerrando a tentativa e reiniciando
  a jornada na Caatinga.

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