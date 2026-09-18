import json

from lxml import etree

from config import base_url,Tool

save_path = Tool.File.path_add_site('data/ml.json')

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.pureology.com',
    'Referer': 'https://www.pureology.com/?__cf_chl_tk=F4fqD5glzJhQjzA8nv7jQFWJIK9v1sVBCAGzfmSL4FE-1786956533-1.0.1.1-GjSK.BgmVjyA_ncYq.fLS9GxTuQvzk419JXvPd6.tU0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Microsoft Edge";v="151", "Chromium";v="151"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"151.0.4129.86"',
    'sec-ch-ua-full-version-list': '"Not=A?Brand";v="99.0.0.0", "Microsoft Edge";v="151.0.4129.86", "Chromium";v="151.0.7922.138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
}
cookies=None
data = {
    'c75dac09af817e88281eeae0d1174c33c7b3b9c8482f05b4d0343c6193a9e6b6': 'uHCipKH7d4sPdY9LoYopI7oA8YVSsx7aXbHU_kD_vTA-1786956533-1.2.1.1-JyFCu8NwKJlkODPKREUgaAtd3kx5KBYs3wd31Vd30544o7eysIwyRprjFEqdAyi5z3L8r_CVy4TWjmh7IJIuv4loBASc7nOIDndZcElU8G4zwk98zS_iE.7YJjDc4oH5UB5uWqsJoD3XxLOyi8BwYAhi_d7qKwFnjDuRzDsV8tZexTSzetQy5ZB2Vn5MLQ_naYuu12vbYiGko2KOsYA0bjfpIBOHyKZnDHsSXswTkPvp5.htgt2V2tr_h9JT9Jrgy6ui5SDS0XeIlzLMhnwSo_YeQimurqUEa0vYOMbfNCBLUd8ThBqhNNop1LXmOHMa65PuRkKTkiaq7xk2M3io3.VL.97Roa2kl.sX.peQhwXUg5aP.rRXjFO4n_mNu7zowQ3udE_FUK0GExln2zeuuvEj1kUUkFoYwDrXOOGtL9swA2tY7NYXGshVgLoZ50tt9Bt0zDLioS7_K98ERKAM6mXFdlERP6D.zuae3HKGGXC9OilsCEPJ4nPFjGmSt0ce06RiCKPTKL668xHzLOZT_jPoTVMcTcjhWk8Vg8cFjGY8ImSwdD38osCdZxslzAUTCg9G1ROQufpJ6HpCztVTItKqDWgv68O8Y.7zAxx88yjfWgLhpZf_o2ln75g4CL_mfbQIFUYHRnJdtR1Hb6cQc59o.MIhfgFQREsJm5myquxvKpOMtftlnerpJj4VHtDaJySu2YDN6YiCKZAWOBxDavsX_wfe7qDGlCUnXVHCb_njVkxwkYCsEL1P0mWYvKnspjgFFv029lHSAH4pyUfRoo4qy8lZPLAbJcKMSBk5Itb1JgaHRRtZ9Z7tiCPH.u.fLPXpiP5EFjzwtN2au8zyj2dUNKkYeqbBjDpPoxWm2auW6sSH_1a7HpuGEpDy96E.DNDPBYUdULzpoTeY1SB1S7l4Z1O0fn6zDNpz6KImu_k64S9E14ppJ8sKJhsHAPnH6KEkp2fucUdCBVLX5pkxiYm83.dzHNp.aN88ZencS9TL4xjNn5k4j4zBi3oyODblcMXQ9oQ9zaIrU0LT.0VNELZ8AIez8llss7y2vvT5IGTb867kqAGZOMJy3SpbH818AfnwXrgLmaqGbc66GbinjnQcw6RfNRfFmd1CbQpBNAxspzb93cqnp0rrB1B9SqpaTwTAgW1eHosrNoNkFhi3nKtxe1TKGIr9D_AIaHjHVWOe6hBHpt3rBeca6SRyDl9EzRsndav..8mNsXkVm5cWvQ',
    'f25cee4904a02cf59e35cecc32a218fe28a2ed8b4651cda01fa6117042908464': 'LkfApmnopQqYa_wEnj59mTJxcLuQFliyJiJFLFYYl8M-1786956533-1.2.1.1-Nryq0rQua9tpigsoxf7lgNccMW4ccs4ZhvO0DqmKUbEEHjjUO2QWxWMI_5UXjHLZckQBhk3_4BAPWEGGSBAhMS8ydMeuLOJzmjOE2r9fNqwY7VecipPfjZ7X.9ha2iSBn7X_KSzMhzK8.gvCngxSrMtxk7SIjMl.Zr4xv.yLA4s8UzlN.ndf4PmuZXiZZ.1etBeLjIHExR5ZHtbzC.mgAi8t5dYtC0m3.ctKhv4GeA1kSBIGK1lZqJO7GoSmmK9QH.csh.bR.Y8jxyWsu6TvGvHvwF.I42tw80lbkjnR784JnP.Eu6u8tn8KX_BP.tfq80CRrx9.ObSjuj_Ey9p2GFrpejU7nVstatqTHnbrMi9s9_qVps7ED3guWqVAuC33jYFWw3nX.nifqajXm1v56Mfvw2m8fvekY3OP_f9cSKeYGlTVS4.e_e.N2qd2AbsjDx7Y8sOnGj9hA24ZJXDlBb3E7xI6UPuqQFJxJa_LiqeYcZo_Etq_0bgnRtT3iMzAHLweN1qn8Lp9dCjmCHo7198P1c6TUKy18tTnuZdaViwtJ4osxuW81u_ZyMJQlUTeg1Wa7uQ16uHQcvHWrCxVoHjJlzbyggknHU.lm3S9u_y9FnuUML6luug1QNcc58x86.0.eq4cIGiPOqRybnS9WpndzcgR5BRuWFca4u4_yVBipFEDplR5YGqDnH.4RYE98yzo9et1LkHHls_FU_LEGmfstUJpvkauV_6aAI6WUSSRjTJiIqHcuewbdiAhMHazsqHqxL8iXjpq.lPixjNXnS0oKJGExCXzGbuwFdFvQs9Rhd8VWYF_ibQGdEaKxUmtq0UNMhs1WxfVvATqaaUIXyCSAXwasJvo9hz5_550mZpS5.q2c4GkL7rtkVUCWFjP',
    '4c93fd2da1d39b5f7798998baed9d79bbb889242442a800276f654a697cfa3b0': 'HjEXjJw9fCGzcUwhxbJuK8958XlaL2.SSCYHOk7d.7w-1786956540-1.0.1.1-uMTKOl2MAIOjznftvhD5XAn7ZL5EolQ2KHdUee_Jw2R_1ZXj69vT0573vardWOp8gyn0e1Kw48mObrzQJzTfUD4tMx5v4zBWb2TORNgqIKvJdoXnzQhU4LT9Qz51TNPkTGJC13v7w_AqUQs3iZJRU2bULM.KQJasc8rt6a7VarvupJTuTiqxtdAbFDk5FgTo',
}


from lxml import etree


def parse_menu(li_elements):
    """
    递归解析菜单项，返回字典 {name: {"url": ..., "child": {...}}}
    """
    result = {}
    for li in li_elements:
        # ----- 提取名称 -----
        # 优先取 span.c-navigation__link-name
        name_elems = li.xpath('.//span[@class="c-navigation__link-name"]')
        if name_elems:
            name = name_elems[0].text.strip()
        else:
            # 次选 a 或 span 的文本
            a_elems = li.xpath('.//a[contains(@class, "c-navigation__link")]')
            if a_elems:
                name = a_elems[0].text.strip()
            else:
                span_elems = li.xpath('.//span[contains(@class, "c-navigation__link")]')
                if span_elems:
                    name = span_elems[0].text.strip()
                else:
                    continue  # 无名称跳过

        # ----- 提取链接 -----
        a_elems = li.xpath('.//a[contains(@class, "c-navigation__link")]')
        url = a_elems[0].get('href') if a_elems and a_elems[0].get('href') else None

        # ----- 查找子菜单（严格匹配该 HTML 结构）-----
        # 情况1：一级菜单的子菜单（包裹在 flyout-element 中）
        child_uls = li.xpath('./div[contains(@class, "c-navigation__flyout-element")]/div[contains(@class, "c-navigation__container")]/ul[contains(@class, "c-navigation__list")]')
        # 情况2：二级及以下菜单的直接子容器（直接 div.c-navigation__container）
        if not child_uls:
            child_uls = li.xpath('./div[contains(@class, "c-navigation__container")]/ul[contains(@class, "c-navigation__list")]')
        # 如果都没有，则无子菜单

        if child_uls:
            # 取第一个 ul（每个菜单项只含一个子菜单 ul）
            child_items = child_uls[0].xpath('./li[contains(@class, "c-navigation__item")]')
            if child_items:
                children = parse_menu(child_items)   # 递归处理子项
            else:
                children = {}
        else:
            children = {}

        # ----- 组装节点 -----
        node = {}
        if url:
            node["url"] = url
        if children:
            node["child"] = children
        # 即使无 url 无 child，也保留名称（空字典，表示该标题无链接也无子项，但实际可能含子项）
        result[name] = node

    return result


dic = {
  "NEW! SMOOTH GLOSS": {
    "url": "https://www.pureology.com/hair-care/smooth-gloss",
    "child": {
      "SHOP SMOOTH GLOSS": {
        "url": "https://www.pureology.com/hair-care/smooth-gloss"
      },
      "LEARN ABOUT SMOOTH GLOSS": {
        "url": "https://www.pureology.com/blog/smooth-gloss-frizz-control-color-treated-hair.html"
      },
      "SHOP BEST SELLERS": {
        "url": "https://www.pureology.com/best-sellers"
      },
      "TAKE OUR HAIR QUIZ": {
        "url": "https://www.pureology.com/hair-care-routine-quiz.html"
      }
    }
  },
  "BEST SELLERS": {
    "url": "https://www.pureology.com/best-sellers",
    "child": {
      "Hydrate Glow Catcher Oil": {
        "url": "https://www.pureology.com/hair-care/hydrate-glow-catcher-oil.html"
      },
      "Strength Cure Dream Healer Serum": {
        "url": "https://www.pureology.com/hair-care/strength-cure-dream-healer-serum-repairing-damaged-hair.html"
      },
      "Hydrate Shampoo and Conditioner Duo": {
        "url": "https://www.pureology.com/hair-care/shampoo-and-conditioner-duos/hydrate-shampoo-and-condition-duo.html"
      },
      "Strength Cure Shampoo and Conditioner Duo": {
        "url": "https://www.pureology.com/hair-care/shampoo-and-conditioner-duos/strength-cure-shampoo-and-conditoner-duo.html"
      },
      "Color Fanatic Multi-Tasking Leave-In Spray": {
        "url": "https://www.pureology.com/hair-care/colour-fanatic-treatment-spray-leave-in.html"
      },
      "Shop All Best Sellers": {
        "url": "https://www.pureology.com/best-sellers"
      }
    }
  },
  "SHOP": {
    "url": "https://www.pureology.com/hair-care",
    "child": {
      "Hair Needs": {
        "child": {
          "Anti-Frizz Smoothing": {
            "url": "https://www.pureology.com/hair-care/anti-frizz-smoothing"
          },
          "Blonde Hair": {
            "url": "https://www.pureology.com/hair-care/blonde-hair"
          },
          "Curly Hair": {
            "url": "https://www.pureology.com/hair-care/curly-hair"
          },
          "Damaged Hair": {
            "url": "https://www.pureology.com/hair-care/damaged-hair"
          },
          "Fine & Thin Hair": {
            "url": "https://www.pureology.com/hair-care/fine-thin-hair"
          },
          "Heat Protection": {
            "url": "https://www.pureology.com/hair-care/heat-protection"
          },
          "Moisturizing": {
            "url": "https://www.pureology.com/hair-care/moisturizing"
          },
          "Shine": {
            "url": "https://www.pureology.com/hair-care/shine"
          },
          "Volume": {
            "url": "https://www.pureology.com/hair-care/volume"
          }
        }
      },
      "Collections": {
        "child": {
          "Hydrate": {
            "url": "https://www.pureology.com/hair-care/hydrate"
          },
          "Smooth Gloss": {
            "url": "https://www.pureology.com/hair-care/smooth-gloss"
          },
          "Color Fanatic": {
            "url": "https://www.pureology.com/hair-care/color-fanatic"
          },
          "Strength Cure": {
            "url": "https://www.pureology.com/hair-care/strength-cure"
          },
          "Nanoworks® Gold": {
            "url": "https://www.pureology.com/hair-care/nano-works-gold"
          },
          "Pure Volume": {
            "url": "https://www.pureology.com/hair-care/pure-volume"
          },
          "Strength Cure Blonde": {
            "url": "https://www.pureology.com/hair-care/strength-cure-best-blonde"
          },
          "Style + Protect": {
            "url": "https://www.pureology.com/styling"
          },
          "Love Luster": {
            "url": "https://www.pureology.com/hair-care/love-luster-hair-perfume"
          },
          "Last Chance": {
            "url": "https://www.pureology.com/hair-care/last-chance"
          }
        }
      },
      "Product Types": {
        "child": {
          "Shampoos": {
            "url": "https://www.pureology.com/hair-care/sulphate-free-shampoos"
          },
          "Conditioners": {
            "url": "https://www.pureology.com/hair-care/conditioners"
          },
          "Treatments & Styling": {
            "url": "https://www.pureology.com/hair-care/treatments-and-styling"
          },
          "Hair Perfume": {
            "url": "https://www.pureology.com/hair-care/love-luster-hair-perfume.html"
          },
          "Shampoo & Conditioner Duos - 10% off": {
            "url": "https://www.pureology.com/hair-care/shampoo-and-conditioner-duos"
          },
          "Liters": {
            "url": "https://www.pureology.com/hair-care/liters"
          },
          "Travel Sizes": {
            "url": "https://www.pureology.com/hair-care/travel-sizes"
          },
          "Value Sets": {
            "url": "https://www.pureology.com/hair-care/value-sets"
          },
          "Build a Bundle - Save 15%": {
            "url": "https://www.pureology.com/create-your-bundle"
          }
        }
      },
      "TREATMENTS & STYLING": {
        "child": {
          "Hair Serums & Oils": {
            "url": "https://www.pureology.com/hair-care/hair-serums-and-oils"
          },
          "Leave-Ins & Primers": {
            "url": "https://www.pureology.com/hair-care/leave-ins"
          },
          "Toners & Glosses": {
            "url": "https://www.pureology.com/hair-care/toners-and-glosses"
          },
          "Hair Masks": {
            "url": "https://www.pureology.com/hair-care/hair-masks-deep-conditioners"
          },
          "Sprays & Creams": {
            "url": "https://www.pureology.com/hair-care/sprays-lotions-creams"
          },
          "Stylers": {
            "url": "https://www.pureology.com/styling"
          }
        }
      }
    }
  },
  "SHAMPOOS & CONDITIONERS": {
    "url": "https://www.pureology.com/shampoos-and-conditioners",
    "child": {
      "SHAMPOOS BY CATEGORY": {
        "child": {
          "Shampoos": {
            "url": "https://www.pureology.com/hair-care/sulphate-free-shampoos"
          },
          "Dry Shampoo": {
            "url": "https://www.pureology.com/styling/refresh-and-go-oil-absorbing-dry-shampoo.html"
          },
          "Travel Size Shampoos": {
            "url": "/hair-care/travel-sizes?prefn1=pureProductType&prefv1=Shampoos"
          },
          "Liter Shampoos": {
            "url": "/hair-care/liters?insertMode=true&prefn1=pureProductType&prefv1=Shampoos&start=0&sz=18"
          },
          "Shampoo & Conditioner Duos - 10% off": {
            "url": "https://www.pureology.com/hair-care/shampoo-and-conditioner-duos"
          },
          "Value Sets": {
            "url": "https://www.pureology.com/hair-care/value-sets"
          },
          "Build a Bundle - Save 15%": {
            "url": "https://www.pureology.com/create-your-bundle"
          }
        }
      },
      "SHAMPOOS BY NEED": {
        "child": {
          "Anti-Frizz Smoothing": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/anti-frizz-smoothing-shampoos"
          },
          "Blonde Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/blonde-hair-shampoos"
          },
          "Curly Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/curly-hair-shampoos"
          },
          "Damaged Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/damaged-hair-shampoos"
          },
          "Fine & Thin Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/fine-thin-hair-shampoos"
          },
          "Moisturizing": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/moisturizing-shampoos"
          },
          "Shine": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/shine-shampoos"
          },
          "Volume": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/volume-shampoos"
          }
        }
      },
      "CONDITIONERS BY CATEGORY": {
        "child": {
          "Conditioners": {
            "url": "https://www.pureology.com/hair-care/conditioners"
          },
          "Travel Size Conditioners": {
            "url": "/hair-care/travel-sizes?prefn1=pureProductType&prefv1=Conditioners"
          },
          "Liter Conditioners": {
            "url": "/hair-care/liters?prefn1=pureProductType&prefv1=Conditioners"
          },
          "Leave-in Conditioner": {
            "url": "https://www.pureology.com/hair-care/colour-fanatic-treatment-spray-leave-in.html"
          },
          "Hair Masks": {
            "url": "https://www.pureology.com/hair-care/hair-masks-deep-conditioners"
          },
          "Shampoo & Conditioner Duos - 10% off": {
            "url": "https://www.pureology.com/hair-care/shampoo-and-conditioner-duos"
          },
          "Build a Bundle - Save 15%": {
            "url": "https://www.pureology.com/create-your-bundle"
          },
          "Value Sets": {
            "url": "https://www.pureology.com/hair-care/value-sets"
          }
        }
      },
      "CONDITIONERS BY NEED": {
        "child": {
          "Anti-Frizz Smoothing": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/anti-frizz-smoothing-conditioners"
          },
          "Blonde Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/blonde-hair-conditioners"
          },
          "Curly Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/curly-hair-conditioners"
          },
          "Damaged Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/damaged-hair-conditioners"
          },
          "Fine & Thin Hair": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/fine-thin-hair-conditioners"
          },
          "Moisturizing": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/moisturizing-conditioners"
          },
          "Shine": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/shine-conditioners"
          },
          "Volume": {
            "url": "https://www.pureology.com/shampoos-and-conditioners/volume-conditioners"
          }
        }
      }
    }
  },
  "HAIR QUIZ": {
    "url": "https://www.pureology.com/hair-quiz.html",
    "child": {
      "Hair Quiz": {
        "child": {
          "Hair Care Quiz": {
            "url": "https://www.pureology.com/hair-care-routine-quiz.html"
          },
          "Hair Treatment Quiz": {
            "url": "https://www.pureology.com/hair-styling-quiz.html"
          }
        }
      }
    }
  },
  "BLOG": {
    "url": "https://www.pureology.com/blog",
    "child": {
      "Hair Care tips": {
        "child": {
          "Unlock Lasting Smoothness": {
            "url": "https://www.pureology.com/blog/smooth-gloss-frizz-control-color-treated-hair.html"
          },
          "Beat the Heat: Your Essential Guide to Summer Haircare": {
            "url": "/blog/summer-haircare-guide-tips.html"
          },
          "What is a Hair Treatment?": {
            "url": "https://www.pureology.com/blog/what-is-a-hair-treatment.html"
          },
          "Everything To Know About Hair Fragrance": {
            "url": "https://www.pureology.com/blog/what-is-a-hair-fragrance.html"
          },
          "Start the New Year with Healthy Hair": {
            "url": "https://www.pureology.com/blog/healthy-hair-tips-new-year.html"
          },
          "Hydrate vs. Hydrate Sheer": {
            "url": "https://www.pureology.com/blog/pureology-hydrate-vs-hydrate-sheer-guide.html"
          },
          "Discover Why You Need A Hair Oil": {
            "url": "https://www.pureology.com/blog/what-is-a-hair-oil-and-do-i-need-it.html"
          },
          "Dream Healer Serum vs. Glow Catcher Oil": {
            "url": "https://www.pureology.com/blog/difference-between-pureology-strength-cure-serum-and-hydrate-glow-hair-oil.html"
          },
          "Award-Winning Formulas": {
            "url": "https://www.pureology.com/blog/award-winning-formulas.html"
          },
          "Discover Color Fanatic": {
            "url": "https://www.pureology.com/blog/color-fanatic-collection.html"
          },
          "Hair Masks & Deep Conditioners": {
            "url": "https://www.pureology.com/blog/hair-masks-deep-conditioner.html"
          },
          "Discover Strength Cure": {
            "url": "https://www.pureology.com/blog/strength-cure-collection.html"
          },
          "Strength Cure vs. Strength Cure Blonde": {
            "url": "https://www.pureology.com/blog/strengthcure-vs-strengthcure-blonde.html"
          },
          "Learn About Sulfate-Free Shampoo": {
            "url": "https://www.pureology.com/blog/sulfate-free-shampoo-benefits-healthy-hair.html"
          },
          "Purple Shampoo: Not Just for Blondes!": {
            "url": "https://www.pureology.com/blog/why-you-need-a-purple-shampoo.html"
          },
          "Discover Nanoworks Gold": {
            "url": "https://www.pureology.com/blog/nanoworks-collection.html"
          },
          "Top Coat Hair Treatments": {
            "url": "https://www.pureology.com/blog/top-coat.html"
          }
        }
      },
      "Styling Hair Tips": {
        "child": {
          "How to Use Dry Shampoo": {
            "url": "https://www.pureology.com/blog/how-to-use-dry-shampoo.html"
          },
          "The Best Styling Products": {
            "url": "https://www.pureology.com/blog/best-styling-product-hair-type.html"
          },
          "The Natural Ingredients You Need ASAP In Your Styling Products": {
            "url": "https://www.pureology.com/blog/natural-vegan-hair-ingredients-styling.html"
          },
          "5 Easy Ways to Protect and Style Your Hair While You Sleep": {
            "url": "https://www.pureology.com/blog/protect-and-style-hair-in-your-sleep.html"
          },
          "4 Workout Essentials You Need In Your Gym Bag": {
            "url": "/blog/workout-essentials-gym-bag.html"
          }
        }
      }
    }
  },
  "OFFERS": {
    "url": "https://www.pureology.com/special-offers.html"
  },
  "PURE REWARDS": {
    "url": "https://www.pureology.com/loyalty.html"
  }
}

# 定位导航

@Tool.zs('数据结构:{title:{url:xxx,child:{title:url}}')
def f1(url_dic):

    url = base_url

    res = Tool.session.post(url,headers=headers,cookies=cookies,data=data)
    Tool.HTML.save(res.text)
    html = etree.HTML(res.text)

    tree = html
    navs = tree.xpath('//nav[contains(@class, "c-navigation")]')
    if navs:
        nav = navs[0]
        level1_items = nav.xpath('.//li[contains(@class, "m-level-1")]')
        final_dict = parse_menu(level1_items)
        # 输出 JSON 以便查看
        print(json.dumps(final_dict, indent=2, ensure_ascii=False))

        # 输出 JSON
        url_dic.update(final_dict)
        return url_dic
    else:
        print("未找到导航")

    return
    ml1 = html.xpath('//ul[@class="c-navigation__list m-level-1"]/li')
    header_node = ml1


    for node in header_node:


        c_node = node.xpath('./div/div/ul/li')
        a_node = node.xpath('./span/a')[0]

        _name,_url = Tool.HTML.get_a_text_and_url(a_node)
        _name = ''.join(_name).strip()
        _url = _url
        _url = Tool.URL.add_site(_url)

        url_dic[_name] = {'url':_url,'child':{}}

        childs = c_node

        f2(url_dic[_name]['child'], childs)
    print(url_dic)
    return url_dic

def f2(dic, childs):
    for child in childs:
        c_node = child.xpath('./div/picture')

        if len(c_node):
            print(len(c_node))

            _a = child.xpath('./div/a')[0]
            _name, _url = Tool.HTML.get_a_text_and_url(_a)
            _url = Tool.URL.add_site(_url)
            dic[_name] = {'url': _url, 'child': {}}

            return





        else:
            _a = child.xpath('./span/a')

            if _a:
                _a = _a[0]

                _name, _url = Tool.HTML.get_a_text_and_url(_a)
                _url = Tool.URL.add_site(_url)
                dic[_name] = {'url': _url, 'child': {}}

                return


        _name = child.xpath('./sapn//text()')

        _name = ''.join(_name).strip()


        dic[_name] = { 'child': {}}

        n_childs_ls = child.xpath('./div/ul/li')
        f3(dic[_name]['child'],n_childs_ls)

    return dic


def f3(dic,childs):
    for child in childs:
        c_a = child.xpath('./span/a')

        c_tx, c_url = Tool.HTML.get_a_text_and_url(c_a[0])
        _name = c_tx
        _url = c_url
        _url = Tool.URL.add_site(_url)

        dic[_name] = {'url': _url, 'child': {}}


def run():
    url_dic = {}
    f1(url_dic)

    Tool.to_ml_json(url_dic,save_path)


if __name__ == '__main__':
    # run()
    def filter_menu_node(node_dict, name_blacklist, url_black_words):
        """
        递归过滤菜单节点
        :param node_dict: 当前一层 {菜单名: {"url":"xxx", "child":{...}}}
        :param name_blacklist: 需要剔除的菜单名称集合
        :param url_black_words: url包含这些字符就剔除
        :return: 过滤后的新字典
        """
        new_node = {}
        for menu_name, info in node_dict.items():
            url = info.get("url")
            # 条件1：名称黑名单直接跳过
            if menu_name in name_blacklist:
                continue
            # 条件2：url存在且命中黑名单关键词，跳过
            if url and any(word in url for word in url_black_words):
                continue

            # 递归处理子child
            child_data = info.get("child", {})
            filtered_child = filter_menu_node(child_data, name_blacklist, url_black_words)

            new_node[menu_name] = {
                "url": url,
                "child": filtered_child
            }
        return new_node


    # ================= 使用 =================
    # 配置过滤规则
    name_black = {"HAIR QUIZ", "BLOG", "OFFERS", "PURE REWARDS"}
    url_black = {"blog/",'.html'}

    # dic 是你原始顶层菜单字典
    r_dic = filter_menu_node(dic, name_black, url_black)


    Tool.to_ml_json(r_dic, save_path)



