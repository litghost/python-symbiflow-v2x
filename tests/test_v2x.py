#!/usr/bin/env python3

import pytest
from pathlib import Path
import os
from functools import cmp_to_key

from v2x import vlog_to_model
from v2x import vlog_to_pbtype
from v2x.xmlinc import xmlinc
from v2x.mux_gen import mux_gen

from vtr_xml_utils import convert


@pytest.fixture(scope="session", autouse=True)
def prepare_files(request):
    mux_gen(outdir='tests/muxes/routing',
            outfilename='rmux',
            datatype='routing',
            width=2,
            split_inputs=True,
            name_output='O',
            name_mux='RMUX',
            name_inputs='I0,I1'
            )
    mux_gen(outdir='tests/vtr/lutff-pair/omux',
            outfilename='omux',
            datatype='routing',
            width=2,
            split_inputs=True,
            name_output='O',
            name_mux='omux',
            name_inputs='L,F'
            )
def order_based_on_deps(left, right):
    # TODO: this is overly simplified sorting over files with dependencies
    # normally it should be solved with use of topological sort
    with open(left, 'r') as leftfile:
        relhref = xmlinc.make_relhref(left, right)
        leftcontent = leftfile.read()
        if relhref in leftcontent:
            return 1
        leftinccount = leftcontent.count('`include')
    with open(right, 'r') as rightfile:
        relhref = xmlinc.make_relhref(right, left)
        rightcontent = rightfile.read()
        if relhref in rightcontent:
            return -1
        rightinccount = rightcontent.count('`include')
    return leftinccount - rightinccount


def find_files(pattern, rootdir):
    return [str(f) for f in Path(os.path.abspath(rootdir)).glob(pattern)]


def get_test_goldens(goldentype, testfile):
    simfiles = sorted(
        sorted(convert.get_filenames_containing('*.sim.v', testfile)),
        key=cmp_to_key(order_based_on_deps))
    goldens = []
    for sim in simfiles:
        res = find_files('golden.' + goldentype, os.path.dirname(sim))
        if len(res) == 1:
            goldens.append(res[0])
    return goldens


def pytest_generate_tests(metafunc):
    if "modelcase" in metafunc.fixturenames:
        models = get_test_goldens('model.xml', __file__)
        metafunc.parametrize("modelcase", models)
    if "pbtypecase" in metafunc.fixturenames:
        models = get_test_goldens('pb_type.xml', __file__)
        metafunc.parametrize("pbtypecase", models)


def test_model_generation_with_vlog_to_model(modelcase):
    """Parametrized test that checks  if the model.xml files produced by the
    vlog_to_model function are valid
    Parameters
    ----------
    modelcase : str
        The filename of the model.xml file that should be produced by the
        corresponding sim.v file
    """
    modelfile = modelcase
    testdatadir = os.path.dirname(modelfile) + '/'
    vlog_filenames = find_files('*.sim.v', testdatadir)
    assert len(vlog_filenames) == 1
    vlog_filename = vlog_filenames[0]
    testname = vlog_filename.split('/')[-1].split('.')[0]
    generatedmodelfile = testdatadir + testname + '.model.xml'
    modelout = vlog_to_model.vlog_to_model([vlog_filename], None, None,
                                           generatedmodelfile)
    with open(generatedmodelfile, 'w') as model:
        model.write(modelout)

    convertedgolden = convert.vtr_stylize_xml(modelfile)
    convertedmodel = convert.vtr_stylize_xml(generatedmodelfile)

    assert convertedmodel == convertedgolden

    with open(generatedmodelfile, 'w') as model:
        model.write(convertedmodel)


def test_pbtype_generation_with_vlog_to_pbtype(pbtypecase):
    """Parametrized test that checks  if the pb_type.xml files produced by the
    vlog_to_pbtype function are valid
    Parameters
    ----------
    pbtypecase : str
        The filename of the pb_type.xml file that should be produced by the
        corresponding sim.v file
    """
    testdatafile = pbtypecase
    testdatadir = os.path.dirname(testdatafile) + '/'
    vlog_filenames = find_files('*.sim.v', testdatadir)
    assert len(vlog_filenames) == 1
    vlog_filename = vlog_filenames[0]
    testname = vlog_filename.split('/')[-1].split('.')[0]
    generatedmodelfile = testdatadir + testname + '.pb_type.xml'
    pbtypeout = vlog_to_pbtype.vlog_to_pbtype([vlog_filename],
                                              generatedmodelfile,
                                              None)
    with open(generatedmodelfile, 'w') as model:
        model.write(pbtypeout)

    convertedgolden = convert.vtr_stylize_xml(testdatafile)
    convertedmodel = convert.vtr_stylize_xml(generatedmodelfile)

    assert convertedmodel == convertedgolden

    with open(generatedmodelfile, 'w') as model:
        model.write(convertedmodel)
