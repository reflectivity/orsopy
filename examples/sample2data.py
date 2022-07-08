"""
python script to illustrate an application of the simple model language.

usage: python3 sample2data.py <stack> [<angle> <time>] [<angle2> <time2>] ...
with <stack> = sample description according to simple model language
     <angle> = sample orientation 'mu' on Amor
     <time>  = counting time
! The intensity and time parameters are wild guesses and will be
!  adjusted to real measurements in the future.

If no angles are given, a set of default angle - time pairs is used.

Output are two graphs:
- the q-dependent flux on the sample for a given angle
- the calculated reflectivity with errorbars
This might help to plan the experiement (angles and counting times).

Not yet implemented is a variable resolution or a reduced divergence.

Jochen Stahn, 2022-03-30
"""

import sys

import numpy as np
import yaml

from matplotlib import pyplot
from refnx.reflect import SLD, ReflectModel, Structure

from orsopy.fileio import model_language


# Parametised intensity distribution on Amor at the sample position as
# function of incoming angle and wavelength. No real parameters, yet!
def Imap(mu):
    theta_t = np.array(np.arange(-0.7, 0.701, 0.01), ndmin=2)
    I_t = np.exp(-(theta_t ** 2) / 1.6)
    lamda_l = np.array(np.arange(3.5, 12.01, 0.01), ndmin=2)
    I_l = np.exp(-((lamda_l - 4) ** 2) / 30)
    q_lt = np.matmul(1 / lamda_l.T, 4.0 * np.pi * np.sin(np.deg2rad(theta_t + mu)))
    I_lt = np.matmul(I_l.T, I_t * np.sin(np.deg2rad(theta_t + mu)))
    return q_lt, I_lt


# generation of a q_z grid with Delta q / q = 2 % for calculation and plotting
def qBins(resolution=0.02, qMin=0.005, qMax=0.42):
    n = np.log(qMax / qMin) / np.log(1.0 + resolution)
    return qMin * (1.0 + resolution) ** np.arange(n)


def main(txt=None):
    # resolution = 0.01
    if txt is None:
        txt = sys.argv[1]
    if txt.endswith(".yml"):
        dtxt = yaml.safe_load(open(txt, "r").read())
        if "data_source" in dtxt:
            dtxt = dtxt["data_source"]
        if "sample" in dtxt:
            dtxt = dtxt["sample"]["model"]
        sample = model_language.SampleModel(**dtxt)
    else:
        sample = model_language.SampleModel(stack=txt)
    # initial model before resolving any names
    # print(repr(sample), '\n')
    # print("\n".join([repr(ss) for ss in sample.resolve_stack()]), '\n')

    layers = sample.resolve_to_layers()
    structure = Structure()
    for li in reversed(layers):
        m = SLD(li.material.get_sld() * 1e6)
        if li.thickness.unit == "nm":
            structure |= m(li.thickness.magnitude * 10.0, li.roughness.magnitude * 10.0)
        else:
            structure |= m(li.thickness.magnitude, li.roughness.magnitude)
    model = ReflectModel(structure, bkg=0.0)

    bins_q = qBins()
    q = (bins_q[:-1] + bins_q[1:]) / 2.0
    R_q = model(q)

    # sample orientation 'mu' and counting time
    if len(sys.argv) > 3:
        mus = np.array(list(zip(sys.argv[2::2], sys.argv[3::2])), dtype=float)
    else:
        mus = np.array([[0.8, 300], [2.3, 6000], [6.0, 18000]], dtype=float)

    pyplot.figure(figsize=(12, 5))

    for mu, tme in mus:

        q_lt, I_lt = Imap(mu)
        q_q = q_lt.flatten()
        I_q = I_lt.flatten()
        p_q, bins = np.histogram(q_q, bins=bins_q, weights=I_q)

        fltr = p_q > 0
        pyplot.subplot(121)
        pyplot.plot(q[fltr], p_q[fltr], linewidth=2.0, label=f"$\\mu$={mu}")

        # sigma = sqrt( R / I )
        sigma_q = np.where(p_q > 1e-4 * R_q, np.sqrt(R_q / (p_q + 1e-40)), 0) / np.sqrt(tme)

        pyplot.subplot(122)
        pyplot.errorbar(
            q[fltr], R_q[fltr], yerr=sigma_q[fltr], lw=0.4, marker="o", ms=2.5, label=f"{tme}s @ $\\mu$={mu}"
        )

    pyplot.subplot(121)
    pyplot.title("incoming intensity vs. q")
    pyplot.xlabel("$q \\,/\\, \\mathrm{Å}^{-1}$")
    pyplot.ylabel("intensity")
    pyplot.legend()

    pyplot.subplot(122)
    pyplot.title("$q_z$ ranges and statistics")
    pyplot.xlabel("$q \\,/\\,\\mathrm{Å}^{-1}$")
    pyplot.ylabel("$\\log_{10}R(q_z)$")
    pyplot.loglog(q, R_q, c="k", lw=1)
    pyplot.text(0.01, 1.2, txt)
    pyplot.legend()

    pyplot.show()


if __name__ == "__main__":
    main()
