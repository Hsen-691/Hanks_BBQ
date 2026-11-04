"""Seed the Hank's BBQ menu (categories + products), bilingual, prices in LL.

Run from the backend/ folder:   .venv\\Scripts\\python seed.py
Idempotent: clears existing categories/products, then inserts the menu.
Customer accounts and past orders are left untouched (order history keeps its
own name/price snapshots).
"""
from app.database import SessionLocal
from app.models import Branch, CartItem, Category, Product

# (name_en, name_ar, address_en, address_ar, whatsapp_number, sort_order)
# whatsapp_number is digits only, international (no +): wa.me/<number>
BRANCHES = [
    ("Borj El Brajneh", "برج البراجنة", "Ain Al Sekka", "عين السكة", "96181600699", 1),
    ("Jnah", "الجناح", "Foodie Land", "فودي لاند", "96181863086", 2),
    ("Khaldah", "خلدة", "Highway, next to Fayyad Sport", "الأوتوستراد، بجانب فياض سبورت", "96176002206", 3),
]

# (key, name_en, name_ar, sort_order)
CATEGORIES = [
    ("offers", "Offers", "عروض", 1),
    ("burgers", "Premium Burgers", "برغر", 2),
    ("subs", "Sandwiches", "سندويشات", 3),
    ("shawarma", "Shawarma", "شاورما", 4),
    ("wraps", "Wraps", "راب", 5),
    ("platters", "Platters", "صحون", 6),
    ("broasted", "Fried Chicken", "فروج بروستد", 7),
    ("pasta", "Pasta", "باستا", 8),
    ("salads", "Salads", "سلطات", 9),
    ("wings", "Wings & Nuggets", "جوانح وناغتس", 10),
    ("mezze", "Appetizers", "مقبلات", 11),
]

# (category_key, name_en, name_ar, price)
PRODUCTS = [
    # ---- Offers / combos ----
    ("offers", "2 Chicken Burgers + Fries", "٢ تشكن برغر + بطاطا", 600000),
    ("offers", "4 Chicken Burgers", "٤ تشكن برغر", 1000000),
    ("offers", "2 Cheese Beef Burgers + Fries", "٢ تشيز برغر لحمة + بطاطا", 800000),
    ("offers", "2 Lebanese Beef Burgers + Fries", "٢ برغر لبناني لحمة + بطاطا", 800000),
    ("offers", "3 Hanks Beef + 2 Chicken Hanks", "٣ هانكس لحمة + ٢ هانكس دجاج", 1600000),
    ("offers", "4 Mozzarella Burgers (Chicken or Beef)", "٤ برغر موزاريلا (دجاج أو لحمة)", 1900000),
    ("offers", "2 Cheese Beef Burgers + 1 Chicken Burger", "٢ تشيز برغر لحمة + ١ تشكن برغر", 900000),
    ("offers", "1 Chicken Burger + 1 Cheese Burger + Fries", "١ تشكن برغر + ١ تشيز برغر + بطاطا", 700000),
    ("offers", "Chicken Breast + Cheese + Chicken Burger", "تشكن بريست + تشيز + تشكن برغر", 900000),
    ("offers", "5 Lebanese Burgers", "٥ برغر لبناني", 1600000),
    ("offers", "Zinger + Fahita", "زنجر + فاهيتا", 800000),
    ("offers", "Offer 2 Zinger", "عرض ٢ زنجر", 800000),
    ("offers", "Offer 3 Zinger", "عرض ٣ زنجر", 1000000),
    ("offers", "Zinger + Combo (Potato + Salad + Soft Drink)", "زنجر + كومبو (بطاطا + سلطة + مشروب)", 850000),
    ("offers", "Zinger + Chicken Sub", "زنجر + تشكن ساب", 800000),
    ("offers", "1 Hotdog", "١ هوت دوغ", 300000),
    ("offers", "4 Hotdogs", "٤ هوت دوغ", 1000000),
    ("offers", "2 Hotdogs + 1 Cheese Beef Burger", "٢ هوت دوغ + ١ تشيز برغر لحمة", 900000),
    ("offers", "1 Hotdog + 1 Chicken Burger + Fries", "١ هوت دوغ + ١ تشكن برغر + بطاطا", 700000),
    ("offers", "2 Hotdogs + 2 Chicken Burgers", "٢ هوت دوغ + ٢ تشكن برغر", 1000000),
    ("offers", "3 Hanks Beef Burgers", "٣ برغر هانكس لحمة", 1000000),
    ("offers", "3 Chicken Hanks", "٣ تشكن هانكس", 800000),
    ("offers", "2 Chicken Hanks + Fries", "٢ تشكن هانكس + بطاطا", 800000),
    ("offers", "2 Hanks Beef Burgers + Fries", "٢ برغر هانكس لحمة + بطاطا", 900000),
    ("offers", "BBQ Burger + Combo (Salad + Potato + Pepsi)", "برغر باربيكيو + كومبو (سلطة + بطاطا + بيبسي)", 900000),
    ("offers", "Tshakin Halloum + Combo (Potato + Pepsi + Salad)", "تشكن حلوم + كومبو (بطاطا + بيبسي + سلطة)", 850000),

    # ---- Premium burgers ----
    ("burgers", "Chicken Burger", "تشكن برغر", 400000),
    ("burgers", "Chicken Breast Burger", "تشكن بريست برغر", 450000),
    ("burgers", "Hanks Chicken Burger", "هانكس تشكن برغر", 450000),
    ("burgers", "Hanks Beef Burger", "هانكس بيف برغر", 500000),
    ("burgers", "Beef Mozzarella Burger", "برغر موزاريلا لحمة", 600000),
    ("burgers", "Chicken Mozzarella Burger", "برغر موزاريلا دجاج", 600000),
    ("burgers", "BBQ Burger", "برغر باربيكيو", 500000),
    ("burgers", "Zinger Burger", "زنجر برغر", 450000),
    ("burgers", "Big Hanks Burger", "بيغ هانكس برغر", 700000),
    ("burgers", "Lady Hanks Burger", "ليدي هانكس برغر", 700000),
    ("burgers", "Crunchy Spiced Burger", "كرانشي سبايسد برغر", 500000),
    ("burgers", "Swiss Mushroom Burger", "سويس مشروم برغر", 600000),
    ("burgers", "Chicken Halloum Burger", "تشكن حلوم برغر", 450000),
    ("burgers", "Beef Halloum Burger", "بيف حلوم برغر", 600000),
    ("burgers", "Lebanese Beef Burger", "برغر لبناني لحمة", 450000),
    ("burgers", "Classic Burger", "كلاسيك برغر", 450000),
    ("burgers", "Buffalo Burger", "بافلو برغر", 550000),
    ("burgers", "Escalope Burger", "اسكالوب برغر", 450000),

    # ---- Sandwiches / grilled subs (1-30) ----
    ("subs", "Fahita", "فاهيتا", 500000),
    ("subs", "Chicken Sub", "تشكن ساب", 450000),
    ("subs", "Chicken Avoca", "تشكن أفوكا", 500000),
    ("subs", "Steak Sub", "ستيك ساب", 600000),
    ("subs", "Mexicana", "مكسيكانا", 450000),
    ("subs", "Fish Fillet", "سمك فيليه", 500000),
    ("subs", "Sujuk", "سجق", 400000),
    ("subs", "Makanek", "مقانق", 400000),
    ("subs", "Potato Sandwich", "بطاطا سندويش", 300000),
    ("subs", "Tuna", "تونا", 400000),
    ("subs", "Philadelphia", "فيلادلفيا", 550000),
    ("subs", "Jaysh w Jebneh", "حيش وجبنة", 450000),
    ("subs", "Francesco", "فرانسيسكو", 450000),
    ("subs", "Crispy", "كريسبي", 500000),
    ("subs", "Cajun", "كايجن", 400000),
    ("subs", "Crab", "كراب", 500000),
    ("subs", "Shrimp", "قريدس", 500000),
    ("subs", "Shrimp Pane", "قريدس بانيه", 500000),
    ("subs", "Escalope", "اسكالوب", 400000),
    ("subs", "Chicken Pesto", "تشكن بيستو", 550000),
    ("subs", "Tawook", "طاووق", 400000),
    ("subs", "Chinese", "تشاينيز", 400000),
    ("subs", "Shrimp & Chicken", "قريدس ودجاج", 550000),
    ("subs", "Hotdog", "هوت دوغ", 300000),
    ("subs", "Shrimp & Crab", "قريدس وكراب", 550000),
    ("subs", "Shrimp with Greens", "قريدس مع خضرة", 500000),
    ("subs", "Rosto", "روستو", 450000),
    ("subs", "Spicy Fish", "سمكة حرة", 400000),
    ("subs", "Liver", "سودة", 400000),
    ("subs", "Chicken", "دجاج", 400000),
    ("subs", "Tshakin Curry", "تشكن كاري", 450000),

    # ---- Shawarma ----
    ("shawarma", "Chicken Turkish Shawarma Sandwich", "سندويش شاورما تركي دجاج", 400000),
    ("shawarma", "Meat Turkish Shawarma Sandwich", "سندويش شاورما تركي لحمة", 500000),
    ("shawarma", "Mix Turkish Shawarma Sandwich", "سندويش شاورما تركي ميكس", 500000),
    ("shawarma", "Chicken Shawarma Sandwich (Small)", "سندويش شاورما دجاج صغير", 250000),
    ("shawarma", "Chicken Shawarma Sandwich (Large)", "سندويش شاورما دجاج كبير", 350000),
    ("shawarma", "Chicken Shawarma Mrakak", "سندويش شاورما دجاج مرقوق", 350000),
    ("shawarma", "Meat Shawarma Sandwich (Small)", "سندويش شاورما لحمة صغير", 350000),
    ("shawarma", "Meat Shawarma Sandwich (Large)", "سندويش شاورما لحمة كبير", 500000),
    ("shawarma", "Meat Shawarma Mrakak", "سندويش شاورما لحمة مرقوق", 500000),
    ("shawarma", "Chicken Shawarma Meal", "وجبة شاورما دجاج", 400000),
    ("shawarma", "Meat Shawarma Meal", "وجبة شاورما لحمة", 500000),
    ("shawarma", "Chicken Shawarma Double Meal", "وجبة شاورما دجاج دوبل", 600000),
    ("shawarma", "Meat Shawarma Double Meal", "وجبة شاورما لحمة دوبل", 700000),
    ("shawarma", "Mix Double Shawarma Meal", "وجبة شاورما دوبل ميكس", 700000),
    ("shawarma", "Chicken Shawarma Faret 200g Meal", "وجبة شاورما فرط دجاج ٢٠٠ غرام", 600000),
    ("shawarma", "Meat Shawarma Faret 200g Meal", "وجبة شاورما فرط لحمة ٢٠٠ غرام", 700000),
    ("shawarma", "Mix Shawarma Faret Meal", "وجبة شاورما فرط مشكل", 700000),
    ("shawarma", "Half Kilo Chicken Shawarma + Fries", "نص كيلو شاورما دجاج مع بطاطا", 900000),
    ("shawarma", "Half Kilo Meat Shawarma + Fries", "نص كيلو شاورما لحمة مع بطاطا", 1300000),
    ("shawarma", "Kilo Chicken Shawarma + Fries", "كيلو شاورما دجاج مع بطاطا", 1500000),
    ("shawarma", "Kilo Meat Shawarma + Fries", "كيلو شاورما لحمة مع بطاطا", 2000000),
    ("shawarma", "3 Chicken Shawarma (Small)", "٣ شاورما دجاج صغار", 600000),
    ("shawarma", "4 Chicken Shawarma (Large)", "٤ شاورما دجاج كبار", 1200000),
    ("shawarma", "2 Meat Shawarma (Small)", "٢ شاورما لحمة صغار", 500000),
    ("shawarma", "3 Meat Shawarma (Large)", "٣ شاورما لحمة كبار", 1200000),
    ("shawarma", "Chicken Shawarma Rocket (Large Bread)", "صاروخ شاورما دجاج خبز عربي كبير", 450000),
    ("shawarma", "Meat Shawarma Rocket (Large Bread)", "صاروخ شاورما لحمة خبز عربي كبير", 600000),

    # ---- Wraps ----
    ("wraps", "Twister", "تويستر", 600000),
    ("wraps", "Chicken Avoca Wrap", "تشكن أفوكا راب", 500000),
    ("wraps", "Chicken Swiss Mushroom Wrap", "تشكن سويس مشروم راب", 600000),
    ("wraps", "Beef Swiss Mushroom Wrap", "بيف سويس مشروم راب", 700000),
    ("wraps", "Buffalo Wrap", "بافلو راب", 400000),
    ("wraps", "Chicken Barbecue Wrap", "تشكن باربيكيو راب", 400000),
    ("wraps", "Mexican Wrap", "مكسيكان راب", 500000),
    ("wraps", "1 Twister + 1 Boneless", "١ تويستر + ١ بونلس", 900000),
    ("wraps", "Hanks Tournedo", "هانكس تورنيدو", 750000),

    # ---- Platters ----
    ("platters", "Chicken Stroganoff with Rice", "صحن ستروغانوف دجاج مع رز", 1000000),
    ("platters", "Beef Stroganoff with Rice", "صحن ستروغانوف لحمة مع رز", 1100000),
    ("platters", "Chicken Curry with Rice", "صحن شيكن كاري مع رز", 1000000),
    ("platters", "Light Chicken Plate", "صحن لايت شيكن", 900000),
    ("platters", "Steak Mushroom Plate", "صحن ستيك مشروم", 1100000),
    ("platters", "Chicken Mushroom Plate", "صحن شيكن مشروم", 1000000),
    ("platters", "Shrimp 12 pcs Plate", "صحن قريدس ١٢ قطعة", 1300000),
    ("platters", "Fish Fillet 3 pcs Plate", "صحن فيليه سمك ٣ قطع", 1100000),
    ("platters", "Chicken Tawook Skewers Plate", "صحن طاووق سيخين", 800000),
    ("platters", "Escalope Plate", "صحن اسكالوب", 800000),
    ("platters", "Chicken Quesadilla Meal", "وجبة كاساديا دجاج", 900000),
    ("platters", "Beef Quesadilla Meal", "وجبة كاساديا لحمة", 1000000),
    ("platters", "Shrimp with Greens Plate", "صحن قريدس مع خضرة", 1300000),
    ("platters", "Boiled Shrimp Plate", "صحن قريدس مسلوق", 1300000),

    # ---- Fried chicken (broasted) ----
    ("broasted", "Half Broasted Chicken (4 pcs)", "نص فروج بروستد ٤ قطع", 900000),
    ("broasted", "Broasted Chicken (8 pcs)", "فروج بروستد ٨ قطع", 1500000),
    ("broasted", "Whole Broasted Chicken", "فروج بروستد كامل", 2500000),
    ("broasted", "Crispy Meal (3 pcs)", "وجبة كرسبي ٣ قطع", 650000),
    ("broasted", "Crispy Meal (5 pcs)", "وجبة كرسبي ٥ قطع", 850000),
    ("broasted", "Crispy Meal (8 pcs)", "وجبة كرسبي ٨ قطع", 1150000),

    # ---- Pasta ----
    ("pasta", "4 Cheese Pasta", "باستا ٤ أجبان", 600000),
    ("pasta", "Fettuccine Alfredo Pasta", "باستا فيتوتشيني ألفريدو", 700000),
    ("pasta", "Pesto Pasta", "باستا بيستو", 700000),
    ("pasta", "Shrimp Pasta", "باستا قريدس", 900000),

    # ---- Salads ----
    ("salads", "Rocca Salad", "سلطة روكا", 450000),
    ("salads", "Fattouch", "فتوش", 450000),
    ("salads", "Tabouleh", "تبولة", 450000),
    ("salads", "Chicken Caesar Salad", "سلطة سيزر دجاج", 500000),
    ("salads", "Crab Salad", "سلطة كراب", 600000),
    ("salads", "Hanks Salad", "سلطة هانكس", 600000),
    ("salads", "Tuna Salad", "سلطة تونا", 600000),

    # ---- Wings & nuggets ----
    ("wings", "Fried Wings (8 pcs)", "جوانح مقلية ٨ قطع", 450000),
    ("wings", "Fried Wings (15 pcs)", "جوانح مقلية ١٥ قطعة", 850000),
    ("wings", "Fried Wings (30 pcs)", "جوانح مقلية ٣٠ قطعة", 1150000),
    ("wings", "Nuggets (5 pcs)", "ناغتس ٥ قطع", 450000),

    # ---- Appetizers / mezze ----
    ("mezze", "Grape Leaves with Greens", "ورق عنب بخضرة", 350000),
    ("mezze", "Moutabal Hummus", "متبل حمص", 250000),
    ("mezze", "Moutabal Beetroot & Eggplant", "متبل باتنجان شمندر", 250000),
]


def run() -> None:
    db = SessionLocal()
    try:
        # Clear the menu (cart items reference products; remove them first).
        db.query(CartItem).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.flush()

        cats: dict[str, Category] = {}
        for key, en, ar, order in CATEGORIES:
            c = Category(name_en=en, name_ar=ar, sort_order=order)
            db.add(c)
            db.flush()
            cats[key] = c

        count_by_cat: dict[str, int] = {}
        for cat_key, en, ar, price in PRODUCTS:
            n = count_by_cat.get(cat_key, 0)
            count_by_cat[cat_key] = n + 1
            db.add(
                Product(
                    category_id=cats[cat_key].id,
                    name_en=en,
                    name_ar=ar,
                    price=price,
                    is_available=True,
                    sort_order=n,
                )
            )

        # Branches are managed in the admin panel, so only seed them if none
        # exist yet (re-running the menu seed won't overwrite your edits).
        branch_msg = "branches already present, left as-is"
        if db.query(Branch).count() == 0:
            for en, ar, addr_en, addr_ar, wa, order in BRANCHES:
                db.add(Branch(
                    name_en=en, name_ar=ar,
                    address_en=addr_en, address_ar=addr_ar,
                    whatsapp_number=wa, sort_order=order, is_active=True,
                ))
            branch_msg = f"seeded {len(BRANCHES)} branches"

        db.commit()
        print(f"Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} products; {branch_msg}.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
