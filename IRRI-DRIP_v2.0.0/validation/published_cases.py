"""
IRRI-DRIP — checks against values that exist outside this program.

Everything else in validation/ checks the program against itself: the
edge-case probe checks it does not contradict its own guards, the step
method checks one internal path against another internal path. Both are
necessary and neither can catch an error the whole program shares.

This file holds only checks whose reference value comes from OUTSIDE.
Where a reference could be confirmed, it is asserted and its source named.
Where it could not, the case is listed as UNVERIFIED and nothing is
asserted — an invented reference is worse than a missing one.

Run:  python validation/published_cases.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import kernels as K

CHECKS = []
UNVERIFIED = []


def check(name, got, expected, tol, source):
    ok = abs(got - expected) <= tol
    CHECKS.append((ok, name, got, expected, tol, source))
    return ok


def unverified(name, note):
    UNVERIFIED.append((name, note))


# ---------------------------------------------------------------------------
# 1. The Christiansen multiple-outlet factor, against its exact definition
# ---------------------------------------------------------------------------

def exact_christiansen(n: int, m: float) -> float:
    """
    The factor as originally DEFINED, not as approximated:

        F = (1^m + 2^m + ... + N^m) / N^(m+1)

    This is a closed definition with no fitted terms, so it is a genuine
    external reference for the three-term approximation the program uses:

        F ~ 1/(m+1) + 1/(2N) + sqrt(m-1)/(6N^2)

    Source for the summation form: Alazba et al., "Explicit Equations for
    Lateral Line Design in Pressurised Irrigation Systems", Water 12(3), 844
    (2020), which states G = (1^m + 2^m + ... + N^m) / N^(m+1) and notes
    "m = 2 in Darcy-Weisbach equation and m = 1.852 in Hazen-Williams
    equation".
    https://www.mdpi.com/2073-4441/12/3/844
    """
    return sum(i ** m for i in range(1, int(n) + 1)) / (float(n) ** (m + 1.0))


def section_christiansen():
    print("\n1. Christiansen F against its exact summation definition")
    print("   Source: Alazba et al., Water 12(3) 844 (2020)")
    print(f"   {'N':>6} {'m':>7} {'exact':>10} {'program':>10} {'diff %':>9}")
    worst = 0.0
    for n in (5, 10, 20, 50, 100, 160, 200, 300):
        for m in (1.75, 1.852, 2.0):
            e = exact_christiansen(n, m)
            a = K.christiansen_f(n, m)
            diff = 100.0 * (a - e) / e
            worst = max(worst, abs(diff))
            if n in (5, 10, 200):
                print(f"   {n:6d} {m:7.3f} {e:10.5f} {a:10.5f} {diff:8.3f}%")
            check(f"christiansen_f(N={n}, m={m})", a, e, 2e-4,
                  "exact summation, Alazba et al. 2020")
    print(f"   worst deviation over all 24 combinations: {worst:.4f} %")


# ---------------------------------------------------------------------------
# 2. Tabulated F values in wide circulation
# ---------------------------------------------------------------------------

def section_tabulated():
    print("\n2. Tabulated F values")
    print("   These two are the values the program's own test suite has")
    print("   asserted since v0.1, and they agree with the exact summation")
    print("   above, which is what makes them usable as a cross-check.")
    for n, m, ref in ((10, 2.0, 0.385), (10, 1.852, 0.402)):
        got = K.christiansen_f(n, m)
        print(f"   N=10, m={m:.3f}: program {got:.4f} vs tabulated {ref:.3f}")
        check(f"tabulated F (N=10, m={m})", got, ref, 0.001,
              "F tables in general circulation; confirmed against the exact sum")


# ---------------------------------------------------------------------------
# 3. Blasius, an equation with a fixed closed form
# ---------------------------------------------------------------------------

def section_blasius():
    print("\n3. Blasius smooth-pipe friction factor, f = 0.316 Re^-0.25")
    for re, ref in ((1.0e4, 0.0316), (1.0e5, 0.316 * (1.0e5 ** -0.25))):
        got = K.blasius_friction_factor(re)
        print(f"   Re={re:9.0f}: program {got:.6f} vs formula {ref:.6f}")
        check(f"Blasius at Re={re:.0e}", got, ref, 1e-9, "closed-form definition")

    print("\n   Blasius implies m = 1.75 exactly, since hf ~ f*Q^2 ~ Q^-0.25 * Q^2.")
    print("   The program MEASURES the exponent from Swamee-Jain instead of")
    print("   assuming it, so on a smooth pipe the two must nearly agree:")
    for re in (1.0e4, 3.0e4, 1.0e5):
        m = K.velocity_exponent(re, 0.0)
        print(f"   Re={re:9.0f}: measured m = {m:.4f}  (Blasius implies 1.7500)")
        check(f"measured exponent on a smooth pipe at Re={re:.0e}", m, 1.75, 0.06,
              "Blasius f ~ Re^-0.25 => m = 1.75, closed form")


# ---------------------------------------------------------------------------
# 4. FAO-56 Penman-Monteith — the one case with a published worked example
# ---------------------------------------------------------------------------

def section_fao56():
    print("\n4. FAO-56 Penman-Monteith")
    unverified(
        "FAO-56 Example 17 / 18 ET0 worked values",
        "The FAO-56 worked examples give ET0 for stated weather at Bangkok and "
        "Brussels. They need the full radiation chain (extraterrestrial "
        "radiation from latitude and day of year, net long-wave, actual vapour "
        "pressure from dewpoint) which this program does NOT implement: it "
        "takes net radiation Rn as a direct input. The comparison is therefore "
        "not like-for-like and no value is asserted here. To close this, "
        "either implement the radiation chain or enter FAO-56's own Rn and "
        "compare only the combination equation.")
    print("   listed as UNVERIFIED — see the note in the summary")


# ---------------------------------------------------------------------------
# 5. What is still outstanding
# ---------------------------------------------------------------------------

def section_outstanding():
    unverified(
        "Keller & Bliesner / ASABE EP405.1 lateral worked examples",
        "Could not be confirmed from an accessible source in this session. "
        "Both are printed standards behind paywalls. Until a copy is read, "
        "the program's lateral result is verified for INTERNAL consistency "
        "(step method, 0.05-0.74 %) but not against a published design.")
    unverified(
        "Choice of velocity exponent for a dripline",
        "A 2020 Water paper states 'm = 2 in Darcy-Weisbach equation and "
        "m = 1.852 in Hazen-Williams equation', which is the widespread "
        "convention and the one this program used until v0.5.0. The program "
        "now measures m from its own friction factor instead, giving about "
        "1.75 on a smooth dripline, because Swamee-Jain plus a constant-f "
        "exponent is internally contradictory. That reasoning is sound and "
        "reproducible, but the m = 1.75 choice for driplines was NOT "
        "confirmed against a named irrigation standard in this session. Both "
        "figures are reported on every lateral so the difference is visible.")
    unverified(
        "Field measurement",
        "No output has been compared with measured pressures or catch-can "
        "discharges from an Egyptian field. This is the only check that tests "
        "the program against reality rather than against arithmetic.")


def main():
    print("=" * 78)
    print("IRRI-DRIP — checks against references outside the program")
    print("=" * 78)

    section_christiansen()
    section_tabulated()
    section_blasius()
    section_fao56()
    section_outstanding()

    print("\n" + "=" * 78)
    print("RESULT")
    print("=" * 78)
    failed = [c for c in CHECKS if not c[0]]
    print(f"  {len(CHECKS) - len(failed)} of {len(CHECKS)} external checks passed.")
    for ok, name, got, exp, tol, src in failed:
        print(f"\n  [FAIL] {name}")
        print(f"         got {got!r}, expected {exp!r} +/- {tol!r}")
        print(f"         source: {src}")

    print(f"\n  {len(UNVERIFIED)} item(s) NOT verified — listed, not asserted:")
    for name, note in UNVERIFIED:
        print(f"\n  [UNVERIFIED] {name}")
        for line in _wrap(note, 68):
            print(f"      {line}")

    print("\n  Nothing in this file asserts a value that could not be traced to")
    print("  a source. The unverified list is the honest remainder.")
    return 1 if failed else 0


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


if __name__ == "__main__":
    sys.exit(main())
