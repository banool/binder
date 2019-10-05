#!/usr/bin/env python3

import argparse
import math
import os
import sys

from reportlab.pdfgen.canvas import Canvas
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl

parser = argparse.ArgumentParser(
    description="Imposer for simple signature bound books."
)
parser.add_argument("file", type=os.path.abspath, help="input pdf file to impose.")
parser.add_argument(
    "--sheets-per-signature",
    type=int,
    default=5,
    help="number of sheets per signature. Each sheet will contain four printed pages of the book.",
)
parser.add_argument(
    "--page-bottom-padding",
    type=float,
    default=0.25,
    help="padding to add to the bottom of the page, in inches.",
)
parser.add_argument(
    "--page-inside-padding",
    type=float,
    default=0.3,
    help="padding to add to the inside of the page (along the spine), in inches.",
)
parser.add_argument(
    "--page-outside-padding",
    type=float,
    default=0.35,
    help="padding to add to the outside of the page (along the face), in inches.",
)
parser.add_argument(
    "--page-offset",
    type=int,
    default=0,
    help="number of pages of the pdf to skip at the start.",
)


def inches_to_dots(inches):
    return inches * 72


def dots_to_inches(dots):
    return float(dots) / 72.0


def get_page_order(total_pages, signature_size):
    pages_per_signature = signature_size * 4
    signatures = int(math.ceil(float(total_pages) / pages_per_signature))

    output = []

    for signature_offset in range(0, total_pages, pages_per_signature):
        top_pointer = signature_offset + pages_per_signature - 1
        bottom_pointer = signature_offset

        for i in range(0, signature_size):
            output.append(top_pointer)
            top_pointer -= 1
            output.append(bottom_pointer)
            bottom_pointer += 1
            output.append(bottom_pointer)
            bottom_pointer += 1
            output.append(top_pointer)
            top_pointer -= 1

    # Filter all page numbers over the total number.
    return [x if x < total_pages else -1 for x in output]


def read_pages(input_filename, page_offset=0):
    pages = PdfReader(input_filename).pages
    pages = pages[page_offset:]
    return [pagexobj(x) for x in pages]


def run(args):
    input_filename = args.file
    output_filename = "book." + os.path.basename(input_filename)
    page_top_line = None

    pages = read_pages(input_filename, page_offset=args.page_offset)
    page_order = get_page_order(len(pages), args.sheets_per_signature)

    canvas = Canvas(output_filename)

    w = inches_to_dots(8.5)
    h = inches_to_dots(11)
    outer_margin = inches_to_dots(args.page_outside_padding)
    inner_margin = inches_to_dots(args.page_inside_padding)
    bottom_margin = inches_to_dots(args.page_bottom_padding)

    x = 0

    for page_num in page_order:
        canvas.setPageSize((w, h))

        target_width = w / 2 - outer_margin - inner_margin

        if page_num >= 0:
            page = pages[page_num]
            canvas.saveState()
            canvas.translate(x, bottom_margin)
            # page.BBox -> (x, y, w, h)
            page_width = page.BBox[2]
            scale = target_width / page_width
            canvas.scale(scale, scale)
            canvas.doForm(makerl(canvas, page))
            canvas.restoreState()

        if x < w / 2:
            # Left of sheet, move to right.
            x = w / 2 + inner_margin
        else:
            # Right of sheet, move to left on next page.
            x = outer_margin

            if page_top_line is not None:
                line_y = inches_to_dots(page_top_line)
                canvas.line(0, line_y, w, line_y)
            canvas.showPage()
    canvas.save()


if __name__ == "__main__":
    run(parser.parse_args())
