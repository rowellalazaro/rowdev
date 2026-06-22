from collections import Counter
from datetime import date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Case, When, IntegerField
from django.db.models.functions import ExtractYear
from django.shortcuts import render

from .models import PDS, Skill, Recognition


def _breakdown(queryset, field, total, top_n=None):
    """Generic count + percentage breakdown for a choice/text field on a queryset."""
    rows = (
        queryset.exclude(**{f"{field}__exact": ""})
                .values(field)
                .annotate(count=Count("id"))
                .order_by("-count")
    )
    rows = [dict(r) for r in rows if r[field]]

    if top_n and len(rows) > top_n:
        head, tail = rows[:top_n], rows[top_n:]
        others_count = sum(r["count"] for r in tail)
        rows = head + [{field: "Others", "count": others_count}]

    for r in rows:
        r["percent"] = round(r["count"] / total * 100, 1) if total else 0
    return rows


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_pds_stats(request):
    qs = PDS.objects.all()
    total = qs.count()

    # ---------- Personal information ----------
    today = date.today()
    age_buckets = qs.exclude(date_of_birth__isnull=True).annotate(
        computed_age=today.year - ExtractYear("date_of_birth")
    ).aggregate(
        b_18_24=Count(Case(When(computed_age__range=(18, 24), then=1), output_field=IntegerField())),
        b_25_34=Count(Case(When(computed_age__range=(25, 34), then=1), output_field=IntegerField())),
        b_35_44=Count(Case(When(computed_age__range=(35, 44), then=1), output_field=IntegerField())),
        b_45_54=Count(Case(When(computed_age__range=(45, 54), then=1), output_field=IntegerField())),
        b_55_up=Count(Case(When(computed_age__gte=55, then=1), output_field=IntegerField())),
    )

    sex_stats = _breakdown(qs, "sex", total)
    civil_status_stats = _breakdown(qs, "civil_status", total)
    citizenship_stats = _breakdown(qs, "citizenship", total)
    blood_type_stats = _breakdown(qs, "blood_type", total)
    religion_stats = _breakdown(qs, "religion", total)

    height_buckets = qs.exclude(height_cm__isnull=True).aggregate(
        under_150=Count(Case(When(height_cm__lt=150, then=1), output_field=IntegerField())),
        b_150_159=Count(Case(When(height_cm__gte=150, height_cm__lt=160, then=1), output_field=IntegerField())),
        b_160_169=Count(Case(When(height_cm__gte=160, height_cm__lt=170, then=1), output_field=IntegerField())),
        b_170_179=Count(Case(When(height_cm__gte=170, height_cm__lt=180, then=1), output_field=IntegerField())),
        b_180_up=Count(Case(When(height_cm__gte=180, then=1), output_field=IntegerField())),
    )

    weight_buckets = qs.exclude(weight_kg__isnull=True).aggregate(
        under_50=Count(Case(When(weight_kg__lt=50, then=1), output_field=IntegerField())),
        b_50_59=Count(Case(When(weight_kg__gte=50, weight_kg__lt=60, then=1), output_field=IntegerField())),
        b_60_69=Count(Case(When(weight_kg__gte=60, weight_kg__lt=70, then=1), output_field=IntegerField())),
        b_70_79=Count(Case(When(weight_kg__gte=70, weight_kg__lt=80, then=1), output_field=IntegerField())),
        b_80_up=Count(Case(When(weight_kg__gte=80, then=1), output_field=IntegerField())),
    )

    # ---------- Location ----------
    province_stats = _breakdown(qs, "res_province", total, top_n=5)
    city_stats = _breakdown(qs, "res_city", total, top_n=8)
    birth_stats = _breakdown(qs, "place_of_birth", total, top_n=5)

    # region is a Python property (derived from res_province), not a DB field,
    # so it can't be aggregated with .values()/.annotate() — count it in Python instead.
    region_counts = Counter(p.region for p in qs.only("res_province"))
    region_stats = [
        {"region": region, "count": count, "percent": round(count / total * 100, 1) if total else 0}
        for region, count in region_counts.most_common()
    ]

    # ---------- Other information ----------
    skill_stats = list(
        Skill.objects.values("category").annotate(count=Count("id")).order_by("-count")
    )

    recognition_total = Recognition.objects.count()
    recognition_stats = list(
        Recognition.objects.values("issuing_body").annotate(count=Count("id")).order_by("-count")[:5]
    )

    context = {
        "total": total,
        "age_buckets": age_buckets,
        "sex_stats": sex_stats,
        "civil_status_stats": civil_status_stats,
        "citizenship_stats": citizenship_stats,
        "blood_type_stats": blood_type_stats,
        "religion_stats": religion_stats,
        "height_buckets": height_buckets,
        "weight_buckets": weight_buckets,
        "province_stats": province_stats,
        "city_stats": city_stats,
        "birth_stats": birth_stats,
        "region_stats": region_stats,
        "skill_stats": skill_stats,
        "recognition_stats": recognition_stats,
        "recognition_total": recognition_total,
    }
    return render(request, "admin_pds_stats.html", context)