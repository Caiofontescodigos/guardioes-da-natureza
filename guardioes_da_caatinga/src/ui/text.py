"""Centralized text rendering helpers.

All text positioning in the game (titles, descriptions, buttons, tooltips,
combat messages, menus...) should go through the helpers in this module so
every text is aligned/centered relative to its own container/card/button and
never depends on fragile magic coordinates.

Convention used everywhere here:

    center_x = container.x + container.width // 2
    center_y = container.y + container.height // 2

Available API:
  - get_font(size)
  - draw_text(surface, text, pos, font_size, color, center, align)
  - draw_text_centered(surface, text, cx, cy, font_size, color)
  - draw_text_left(surface, text, pos, font_size, color)
  - draw_text_right(surface, text, pos, font_size, color)
  - draw_text_centered_in_rect(surface, text, rect, font_size, color)
  - wrap_text(text, font_size, max_width)
  - wrap_text_chars(text, max_chars)
  - measure_block(items)
  - draw_text_block(surface, lines, rect, line_spacing, align)
  - draw_text_block_colored(surface, items, rect, line_spacing, align)
  - draw_multiline_centered(surface, text, rect, font_size, color, ...)
  - draw_fitted_text(surface, text, rect, font_size, color, ...)
  - draw_button_text(surface, text, rect, color, font_size)
"""
import pygame
from config import WHITE, BLACK

_FONT_CACHE = {}

# Standard paddings (please keep using the same everywhere).
TEXT_PAD = 6          # breathing room used around text inside panels/cards
BUTTON_PAD = 8        # padding used inside buttons
DEFAULT_SPACING = 4   # extra vertical gap between wrapped lines


def get_font(size):
    size = max(1, int(size))
    font = _FONT_CACHE.get(size)
    if font is None:
        font = pygame.font.Font(None, size)
        _FONT_CACHE[size] = font
    return font


def text_size(text, font_size):
    return get_font(font_size).size(str(text))


# ---------------------------------------------------------------------------
# Basic (single line) drawing helpers
# ---------------------------------------------------------------------------

def draw_text(surface, text, pos, font_size=24, color=WHITE, center=False,
              align="left"):
    """Draw a single line of text.

    pos is always the anchor point. When ``center`` is True the text is
    centered on both axes on pos. Otherwise ``align`` decides the horizontal
    anchor (``left``/``right``) and pos is the vertical center of the line.
    """
    font = get_font(font_size)
    surf = font.render(str(text), True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (int(pos[0]), int(pos[1]))
    else:
        if align == "right":
            rect.right = int(pos[0])
        else:
            rect.left = int(pos[0])
        rect.centery = int(pos[1])
    surface.blit(surf, rect)
    return rect


def draw_text_centered(surface, text, cx, cy, font_size=24, color=WHITE):
    """Draw a single line centered horizontally and vertically on (cx, cy)."""
    return draw_text(surface, text, (cx, cy), font_size, color, center=True)


def draw_text_left(surface, text, pos, font_size=24, color=WHITE):
    """Draw a single line left-anchored on pos (vertical center)."""
    return draw_text(surface, text, pos, font_size, color, center=False,
                     align="left")


def draw_text_right(surface, text, pos, font_size=24, color=WHITE):
    """Draw a single line right-anchored on pos (vertical center)."""
    return draw_text(surface, text, pos, font_size, color, center=False,
                     align="right")


def draw_text_centered_in_rect(surface, text, rect, font_size=24, color=WHITE,
                               shrink=True, min_font=12):
    """Draw a single line perfectly centered inside a rect.

    If the text is wider than the rect, the font is reduced until it fits.
    """
    rect = pygame.Rect(rect)
    max_w = max(1, rect.w - BUTTON_PAD * 2)
    size = font_size
    if shrink:
        while size > min_font and get_font(size).size(str(text))[0] > max_w:
            size -= 1
    return draw_text_centered(surface, text, rect.centerx, rect.centery,
                              size, color)


# ---------------------------------------------------------------------------
# Wrapping / multi-line helpers
# ---------------------------------------------------------------------------

def wrap_text(text, font_size, max_width):
    """Wrap ``text`` to fit a pixel ``max_width`` using a given font size.

    Very long single words are broken apart so lines never overflow.
    Returns a list of strings (may be empty for empty text).
    """
    font = get_font(font_size)
    lines = []
    cur = ""
    for word in str(text).split():
        # Break words that are wider than the whole line.
        while font.size(word)[0] > max_width and len(word) > 1:
            lo, hi = 0, len(word)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if font.size(word[:mid])[0] <= max_width:
                    lo = mid
                else:
                    hi = mid - 1
            cut = max(1, lo)
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(word[:cut])
            word = word[cut:]
        if not word:
            continue
        test = cur + " " + word if cur else word
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrap_text_chars(text, max_chars=40):
    """Simple character-count wrapping (kept for compatibility)."""
    lines = []
    cur = ""
    for word in str(text).split():
        test = (cur + " " + word) if cur else word
        if len(test) > max_chars:
            if cur:
                lines.append(cur)
            cur = word
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def measure_block(items, line_spacing=DEFAULT_SPACING):
    """Return (width, height) of a list of (text, font_size, color) items."""
    if not items:
        return (0, 0)
    width = 0
    height = 0
    for text, size, _color in items:
        w, h = get_font(size).size(str(text))
        width = max(width, w)
        height += h
    height += line_spacing * (len(items) - 1)
    return (width, height)


def draw_text_block(surface, lines, rect, font_size=24, color=WHITE,
                    line_spacing=DEFAULT_SPACING, align="center",
                    max_lines=None):
    """Draw a whole block of lines centered inside ``rect``.

    The block is treated as one unit: its total height is measured first and
    the entire group is distributed around the vertical center of the rect.
    With ``align="center"`` every line is horizontally centered; with
    ``align="center_x"`` the block respects the rect width when centering.

    Returns the list of blitted rects.
    """
    pad = TEXT_PAD
    inner = pygame.Rect(rect.x + pad, rect.y + pad,
                        max(1, rect.w - 2 * pad), max(1, rect.h - 2 * pad))
    if max_lines is not None:
        lines = lines[:max_lines]
    drawn = []
    if not lines:
        return drawn

    surfs = [get_font(font_size).render(str(line), True, color)
             for line in lines]
    heights = [s.get_height() for s in surfs]
    spacing = line_spacing if len(surfs) > 1 else 0
    total_h = sum(heights) + spacing * (len(surfs) - 1)

    y = inner.centery - total_h // 2
    if y < inner.y:
        y = inner.y
    if y + total_h > inner.bottom:
        y = inner.bottom - total_h
        if y < inner.y:
            y = inner.y

    for surf, h in zip(surfs, heights):
        x = inner.centerx - surf.get_width() // 2
        rect_out = surf.get_rect(topleft=(x, y))
        surface.blit(surf, rect_out)
        drawn.append(rect_out)
        y += h + spacing
    return drawn


def draw_text_block_colored(surface, items, rect, line_spacing=DEFAULT_SPACING,
                            align="center", max_lines=None):
    """Like draw_text_block but every line may use its own font/color.

    items: list of (text, font_size, color).
    """
    pad = TEXT_PAD
    inner = pygame.Rect(rect.x + pad, rect.y + pad,
                        max(1, rect.w - 2 * pad), max(1, rect.h - 2 * pad))
    if max_lines is not None:
        items = items[:max_lines]
    drawn = []
    if not items:
        return drawn

    surfs = [get_font(size).render(str(text), True, color)
             for text, size, color in items]
    heights = [s.get_height() for s in surfs]
    spacing = line_spacing if len(surfs) > 1 else 0
    total_h = sum(heights) + spacing * (len(surfs) - 1)

    y = inner.centery - total_h // 2
    if y < inner.y:
        y = inner.y
    if y + total_h > inner.bottom:
        y = inner.bottom - total_h
        if y < inner.y:
            y = inner.y

    for surf, h in zip(surfs, heights):
        x = inner.centerx - surf.get_width() // 2
        rect_out = surf.get_rect(topleft=(x, y))
        surface.blit(surf, rect_out)
        drawn.append(rect_out)
        y += h + spacing
    return drawn


def draw_multiline_centered(surface, text, rect, font_size=24, color=WHITE,
                            line_spacing=DEFAULT_SPACING, max_lines=None,
                            align="center"):
    """Wrap ``text`` to fit ``rect`` and draw the whole block centered in it."""
    pad = TEXT_PAD
    max_w = max(1, rect.w - 2 * pad)
    lines = wrap_text(text, font_size, max_w)
    return draw_text_block(surface, lines, rect, font_size, color,
                           line_spacing, align, max_lines)


def draw_fitted_text(surface, text, rect, font_size=24, color=WHITE,
                     min_font=10, max_lines=None, line_spacing=DEFAULT_SPACING):
    """Draw ``text`` wrapped inside ``rect``, reducing the font only when
    necessary so the block always fits both width and height."""
    pad = TEXT_PAD
    inner_w = max(8, rect.w - 2 * pad)
    inner_h = max(8, rect.h - 2 * pad)

    best = None
    for size in range(font_size, min_font - 1, -1):
        lines = wrap_text(text, size, inner_w)
        if not lines:
            continue
        if max_lines is not None:
            lines = lines[:max_lines]
        line_h = get_font(size).get_height()
        total_h = len(lines) * line_h + line_spacing * (len(lines) - 1)
        if total_h <= inner_h:
            best = (size, lines)
            break
    if best is None:
        size = min_font
        lines = wrap_text(text, size, inner_w)
        if max_lines is not None:
            lines = lines[:max_lines]
        best = (size, lines)

    size, lines = best
    return draw_text_block(surface, lines, rect, size, color, line_spacing)


def draw_button_text(surface, text, rect, color=WHITE, font_size=24,
                     min_font=11, max_lines=2):
    """Draw button label centered (horizontal + vertical) inside ``rect``.

    The font is shrunk if needed and the text can wrap into at most two lines
    without ever overflowing the button.
    """
    rect = pygame.Rect(rect)
    inner = pygame.Rect(rect.x + BUTTON_PAD, rect.y,
                        max(1, rect.w - BUTTON_PAD * 2), rect.h)
    return draw_fitted_text(surface, text, inner, font_size=font_size,
                            color=color, min_font=min_font,
                            max_lines=max_lines,
                            line_spacing=2)