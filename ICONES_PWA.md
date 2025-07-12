# Como Adicionar Ícones PWA

## Problema
O sistema está funcionando perfeitamente, mas os ícones do PWA estão faltando, causando erros 404.

## Solução

### Opção 1: Gerador Online (Recomendado)
1. Acesse: https://www.pwabuilder.com/imageGenerator
2. Faça upload de uma imagem (preferencialmente 512x512px)
3. Baixe os ícones gerados
4. Coloque na pasta `static/icons/`

### Opção 2: Criar Ícones Manuais
Crie os seguintes arquivos PNG na pasta `static/icons/`:
- `icon-16x16.png` (16x16 pixels)
- `icon-32x32.png` (32x32 pixels)
- `icon-192x192.png` (192x192 pixels)
- `icon-512x512.png` (512x512 pixels)

### Opção 3: Usar Ícones Temporários
Você pode usar qualquer ícone PNG e renomear para os nomes acima.

## Estrutura Final
```
static/icons/
├── icon-16x16.png
├── icon-32x32.png
├── icon-192x192.png
└── icon-512x512.png
```

## Teste
Após adicionar os ícones, recarregue a página e os erros 404 devem desaparecer.

## Nota
Os ícones são necessários apenas para a funcionalidade PWA (instalação no Android). O sistema funciona perfeitamente sem eles. 