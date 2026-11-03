import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import database
import matcher

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campus-lost-found-secret-key-workshop-2025")

# Ensure database is initialized upon startup
database.init_db()

CATEGORIES = [
    "Electronics",
    "Books & Stationery",
    "Clothing & Apparel",
    "ID Cards & Wallets",
    "Keys & Keychains",
    "Bags & Backpacks",
    "Personal Accessories",
    "Sports Equipment",
    "Other",
]


@app.context_processor
def inject_global_data():
    """Provides common variables across templates."""
    stats = database.get_dashboard_stats()
    return {"stats": stats, "categories": CATEGORIES}


@app.route("/")
def index():
    """Dashboard homepage with stats, recent lost & found items, and match highlights."""
    stats = database.get_dashboard_stats()
    recent_lost = database.get_items(item_type="lost")[:5]
    recent_found = database.get_items(item_type="found")[:5]

    # Calculate active potential matches count
    active_lost = database.get_items(item_type="lost", status="Active")
    active_found = database.get_items(item_type="found", status="Active")
    all_matches = matcher.compute_matches(active_lost, active_found, threshold=0.20)

    top_matches = all_matches[:3]

    return render_template(
        "index.html",
        stats=stats,
        recent_lost=recent_lost,
        recent_found=recent_found,
        top_matches=top_matches,
        total_matches_count=len(all_matches),
    )


@app.route("/report/lost", methods=["GET", "POST"])
def report_lost():
    """Form to submit a lost item report."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        color = request.form.get("color", "").strip()
        description = request.form.get("description", "").strip()
        date_reported = request.form.get("date_reported", "").strip()
        location = request.form.get("location", "").strip()
        contact_info = request.form.get("contact_info", "").strip()

        if not (title and category and color and description and date_reported and location):
            flash("Please fill in all required fields marked with *", "danger")
            return render_template(
                "report_lost.html",
                form_data=request.form,
            )

        item_id = database.create_item(
            item_type="lost",
            title=title,
            category=category,
            color=color,
            description=description,
            date_reported=date_reported,
            location=location,
            contact_info=contact_info,
        )

        flash("Lost item report submitted successfully! Checking for smart matches...", "success")
        return redirect(url_for("item_detail", item_id=item_id))

    return render_template("report_lost.html", form_data={})


@app.route("/report/found", methods=["GET", "POST"])
def report_found():
    """Form to submit a found item report."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        color = request.form.get("color", "").strip()
        description = request.form.get("description", "").strip()
        date_reported = request.form.get("date_reported", "").strip()
        location = request.form.get("location", "").strip()
        contact_info = request.form.get("contact_info", "").strip()

        if not (title and category and color and description and date_reported and location):
            flash("Please fill in all required fields marked with *", "danger")
            return render_template(
                "report_found.html",
                form_data=request.form,
            )

        item_id = database.create_item(
            item_type="found",
            title=title,
            category=category,
            color=color,
            description=description,
            date_reported=date_reported,
            location=location,
            contact_info=contact_info,
        )

        flash("Found item report submitted successfully! Thank you for being a good citizen.", "success")
        return redirect(url_for("item_detail", item_id=item_id))

    return render_template("report_found.html", form_data={})


@app.route("/items")
def items():
    """Displays all lost and found items in separate sections with filtering."""
    item_type_filter = request.args.get("type", "all")
    category_filter = request.args.get("category", "all")
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip()

    kwargs = {}
    if category_filter != "all":
        kwargs["category"] = category_filter
    if status_filter != "all":
        kwargs["status"] = status_filter
    if search_query:
        kwargs["search_query"] = search_query

    lost_items = database.get_items(item_type="lost", **kwargs)
    found_items = database.get_items(item_type="found", **kwargs)

    return render_template(
        "items.html",
        lost_items=lost_items,
        found_items=found_items,
        current_type=item_type_filter,
        current_category=category_filter,
        current_status=status_filter,
        search_query=search_query,
    )


@app.route("/matches")
def matches():
    """Displays smart matches computed across active lost and found items."""
    threshold = float(request.args.get("threshold", "0.20"))
    active_lost = database.get_items(item_type="lost", status="Active")
    active_found = database.get_items(item_type="found", status="Active")

    all_matches = matcher.compute_matches(active_lost, active_found, threshold=threshold)

    return render_template(
        "matches.html",
        matches=all_matches,
        threshold=threshold,
        active_lost_count=len(active_lost),
        active_found_count=len(active_found),
    )


@app.route("/item/<int:item_id>")
def item_detail(item_id):
    """View details of a specific item alongside smart candidate matches."""
    item = database.get_item_by_id(item_id)
    if not item:
        flash("Item not found.", "warning")
        return redirect(url_for("items"))

    # Find candidates
    opposite_type = "found" if item["type"] == "lost" else "lost"
    candidates = database.get_items(item_type=opposite_type, status="Active")
    item_matches = matcher.find_matches_for_item(item, candidates, threshold=0.15)

    return render_template(
        "item_detail.html",
        item=item,
        matches=item_matches,
    )


@app.route("/item/<int:item_id>/status", methods=["POST"])
def update_status(item_id):
    """Update item status to 'Returned' or 'Active'."""
    item = database.get_item_by_id(item_id)
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for("items"))

    new_status = request.form.get("status")
    if new_status not in ("Active", "Returned"):
        new_status = "Returned" if item["status"] == "Active" else "Active"

    database.update_item_status(item_id, new_status)
    flash(f"Item #{item_id} marked as {new_status}!", "success")

    # Redirect back to referring page or item detail
    referer = request.headers.get("Referer")
    if referer:
        return redirect(referer)
    return redirect(url_for("item_detail", item_id=item_id))


@app.route("/api/matches")
def api_matches():
    """JSON API endpoint returning match results for dynamic dashboard updates."""
    active_lost = database.get_items(item_type="lost", status="Active")
    active_found = database.get_items(item_type="found", status="Active")
    all_matches = matcher.compute_matches(active_lost, active_found, threshold=0.15)

    return jsonify({
        "status": "success",
        "count": len(all_matches),
        "matches": [
            {
                "lost_id": m["lost_item"]["id"],
                "lost_title": m["lost_item"]["title"],
                "found_id": m["found_item"]["id"],
                "found_title": m["found_item"]["title"],
                "percentage": m["percentage"],
                "shared_keywords": m["shared_keywords"],
            }
            for m in all_matches
        ],
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
