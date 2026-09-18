import unittest

import pandas as pd
from lxml import etree

from _ljp.html_utils import HTML


class HtmlCleaningTests(unittest.TestCase):
    def test_plain_text_is_returned_as_a_paragraph_html_string(self):
        self.assertEqual(
            HTML.clean_product_desc_str('Customer-ready product description'),
            '<p>Customer-ready product description</p>',
        )

    def test_root_inline_content_is_wrapped_without_losing_formatting(self):
        self.assertEqual(
            HTML.clean_product_desc_str('Intro <strong>important detail</strong> after'),
            '<p>Intro <strong>important detail</strong> after</p>',
        )

    def test_inline_only_content_is_wrapped_in_a_paragraph(self):
        self.assertEqual(
            HTML.clean_product_desc_str('<strong>important detail</strong>'),
            '<p><strong>important detail</strong></p>',
        )

    def test_existing_rich_text_blocks_are_preserved(self):
        self.assertEqual(
            HTML.clean_product_desc_str('<p>Intro</p><ul><li>Feature</li></ul>'),
            '<p>Intro</p><ul><li>Feature</li></ul>',
        )

    def test_nested_divs_preserve_each_visible_paragraph(self):
        self.assertEqual(
            HTML.clean_product_desc_str(
                '<div><div>First paragraph</div>'
                '<div>Second <strong>paragraph</strong></div></div>'
            ),
            '<p>First paragraph</p><p>Second <strong>paragraph</strong></p>',
        )

    def test_nested_divs_keep_text_and_list_boundaries(self):
        self.assertEqual(
            HTML.clean_product_desc_str(
                '<div>Lead text<div>Nested text</div>Trailing text'
                '<div><ul><li>Feature</li></ul></div></div>'
            ),
            '<p>Lead text</p><p>Nested text</p><p>Trailing text</p>'
            '<ul><li>Feature</li></ul>',
        )

    def test_dataframe_cleaning_returns_wrapped_html_strings(self):
        cleaned = HTML.clean_text_fields_df(
            pd.DataFrame({'Description': ['Plain product text']}),
        )

        self.assertEqual(cleaned.loc[0, 'Description'], '<p>Plain product text</p>')

    def test_tree_cleaning_does_not_mutate_sibling_accordion_content(self):
        tree = etree.HTML(
            '<main>'
            '<div data-component="accordion">'
            '<div><h3><button><span>How To Use</span></button></h3></div>'
            '<div><div>Use this product</div></div>'
            '</div>'
            '<div data-component="accordion">'
            '<div><h3><button><span>Ingredients</span></button></h3></div>'
            '<div><div>Water and minerals</div></div>'
            '</div>'
            '</main>'
        )
        accordions = tree.xpath('//div[@data-component="accordion"]')

        how_to_use = HTML.clean_product_desc(accordions[0].xpath('./div[2]')[0])
        ingredients = HTML.clean_product_desc(accordions[1].xpath('./div[2]')[0])

        self.assertIn('Use this product', how_to_use)
        self.assertIn('Water and minerals', ingredients)
        self.assertEqual(
            tree.xpath('//div[@data-component="accordion"]//h3/button/span/text()'),
            ['How To Use', 'Ingredients'],
        )


if __name__ == '__main__':
    unittest.main()
