# Imagens do jogo

As imagens estao separadas por tipo e estilo. O `AssetManager` procura os
arquivos recursivamente, entao novas subpastas podem ser criadas desde que os
nomes dos arquivos continuem unicos.

```
Imagensjogo/
├── animais/                 Sprites dos animais jogaveis
├── inimigos/                Sprites das criaturas inimigas
│   └── conceitos/           Artes conceituais de inimigos (nao usadas no jogo)
├── fundos/                  Cenarios de fundo
│   ├── menu/                Tela inicial atual e a antiga
│   ├── combate/             Cenario das batalhas
│   ├── eventos/             Eventos, acampamento, level up e resgate
│   └── loja/                Cenario da loja
├── mapas/                   Mapa generico da jornada
│   └── regioes/             Artes do mapa por bioma e fase de chefe
├── interface/               Elementos de interface
│   ├── botoes_menu/         Botoes ilustrados do menu principal
│   ├── botoes_ui/           Botoes de navegacao das telas
│   └── icones_mapa/         Icones dos nos do mapa
└── referencias/             Artes antigas/de referencia sem uso no jogo
```
