#################################################################################
# The Institute for the Design of Advanced Energy Systems Integrated Platform
# Framework (IDAES IP) was produced under the DOE Institute for the
# Design of Advanced Energy Systems (IDAES), and is copyright (c) 2018-2021
# by the software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia University
# Research Corporation, et al.  All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and
# license information.
#################################################################################
"""
Tests for solvent reboiler unit model.
Authors: Andrew Lee
"""

import pytest
from pyomo.environ import (ConcreteModel,
                           Constraint,
                           Param,
                           TerminationCondition,
                           SolverStatus,
                           units,
                           value,
                           Var)
from idaes.core import (FlowsheetBlock,
                        MaterialBalanceType,
                        EnergyBalanceType,
                        MomentumBalanceType)
from idaes.generic_models.properties.core.generic.generic_property import (
        GenericParameterBlock)
from idaes.core.util.model_statistics import (degrees_of_freedom,
                                              number_variables,
                                              number_total_constraints,
                                              number_unused_variables)
from idaes.core.util.testing import initialization_tester
from idaes.core.util import get_solver
from pyomo.util.check_units import (assert_units_consistent,
                                    assert_units_equivalent)

from idaes.generic_models.unit_models.column_models.solvent_reboiler import (
    SolventReboiler)
from idaes.power_generation.carbon_capture.mea_solvent_system.properties.MEA_solvent \
    import configuration as aqueous_mea
from idaes.power_generation.carbon_capture.mea_solvent_system.properties.MEA_vapor \
    import flue_gas, wet_co2


# -----------------------------------------------------------------------------
# Get default solver for testing
solver = get_solver()


# -----------------------------------------------------------------------------
class TestAbsorber(object):
    @pytest.fixture(scope="class")
    def model(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.liquid_properties = GenericParameterBlock(default=aqueous_mea)
        m.fs.vapor_properties = GenericParameterBlock(default=flue_gas)

        m.fs.unit = SolventReboiler(default={
            "liquid_property_package": m.fs.liquid_properties,
            "vapor_property_package": m.fs.vapor_properties})

        m.fs.unit.inlet.flow_mol[0].fix(83.89)
        m.fs.unit.inlet.temperature[0].fix(392.5)
        m.fs.unit.inlet.pressure[0].fix(183700)
        m.fs.unit.inlet.mole_frac_comp[0, "CO2"].fix(0.0326)
        m.fs.unit.inlet.mole_frac_comp[0, "H2O"].fix(0.8589)
        m.fs.unit.inlet.mole_frac_comp[0, "MEA"].fix(0.1085)

        m.fs.unit.heat_duty.fix(430.61)

        return m

    @pytest.mark.build
    @pytest.mark.unit
    def test_build(self, model):

        assert hasattr(model.fs.unit, "inlet")
        assert len(model.fs.unit.inlet.vars) == 4
        assert hasattr(model.fs.unit.inlet, "flow_mol")
        assert hasattr(model.fs.unit.inlet, "mole_frac_comp")
        assert hasattr(model.fs.unit.inlet, "temperature")
        assert hasattr(model.fs.unit.inlet, "pressure")

        assert hasattr(model.fs.unit, "bottoms")
        assert len(model.fs.unit.bottoms.vars) == 4
        assert hasattr(model.fs.unit.bottoms, "flow_mol")
        assert hasattr(model.fs.unit.bottoms, "mole_frac_comp")
        assert hasattr(model.fs.unit.bottoms, "temperature")
        assert hasattr(model.fs.unit.bottoms, "pressure")

        assert hasattr(model.fs.unit, "vapor_reboil")
        assert len(model.fs.unit.vapor_reboil.vars) == 4
        assert hasattr(model.fs.unit.vapor_reboil, "flow_mol")
        assert hasattr(model.fs.unit.vapor_reboil, "mole_frac_comp")
        assert hasattr(model.fs.unit.vapor_reboil, "temperature")
        assert hasattr(model.fs.unit.vapor_reboil, "pressure")

        assert isinstance(model.fs.unit.unit_material_balance, Constraint)
        assert isinstance(model.fs.unit.unit_enthalpy_balance, Constraint)
        assert isinstance(model.fs.unit.unit_temperature_equality, Constraint)
        assert isinstance(model.fs.unit.unit_pressure_balance, Constraint)
        assert isinstance(model.fs.unit.zero_flow_param, Param)

        assert number_variables(model.fs.unit) == 84
        assert number_total_constraints(model.fs.unit) == 77
        assert number_unused_variables(model.fs.unit) == 0

    @pytest.mark.component
    def test_units(self, model):
        assert_units_consistent(model)
        assert_units_equivalent(model.fs.unit.heat_duty[0], units.W)

    @pytest.mark.unit
    def test_dof(self, model):
        assert degrees_of_freedom(model) == 0

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.component
    def test_initialize(self, model):
        initialization_tester(model,
                              liquid_state_args={"pressure": 183700,
                                                 "temperature": 393.8,
                                                 "flow_mol": 74.33,
                                                 "mole_frac_comp": {
                                                     "CO2": 0.0285,
                                                     "H2O": 0.8491,
                                                     "MEA": 0.1224}},
                              vapor_state_args={"pressure": 183700,
                                                "temperature": 393.8,
                                                "flow_mol": 9.56,
                                                "mole_frac_comp": {
                                                    "CO2": 0.0645,
                                                    "H2O": 0.9355,
                                                    "N2": 1e-8,
                                                    "O2": 1e-8}})
        # model.fs.unit.display()
        model.fs.unit.liquid_phase.properties_out[0].fug_phase_comp.display()
        model.fs.unit.vapor_phase[0].fug_phase_comp.display()
        model.fs.unit.liquid_phase.properties_out[0].mole_frac_phase_comp_true.display()
        model.fs.unit.liquid_phase.properties_out[0].mole_frac_phase_comp_apparent.display()
        assert False

    # @pytest.mark.solver
    # @pytest.mark.skipif(solver is None, reason="Solver not available")
    # @pytest.mark.component
    # def test_solve(self, model):
    #     results = solver.solve(model)

    #     # Check for optimal solution
    #     assert results.solver.termination_condition == \
    #         TerminationCondition.optimal
    #     assert results.solver.status == SolverStatus.ok

    # @pytest.mark.solver
    # @pytest.mark.skipif(solver is None, reason="Solver not available")
    # @pytest.mark.component
    # def test_solution(self, model):
    #     assert (pytest.approx(101325.0, abs=1e-2) ==
    #             value(model.fs.unit.outlet.pressure[0]))
    #     assert (pytest.approx(304.09, abs=1e-2) ==
    #             value(model.fs.unit.outlet.temperature[0]))
    #     assert (pytest.approx(20.32, abs=1e-2) ==
    #             value(model.fs.unit.outlet.conc_mol_comp[0, "EthylAcetate"]))

    # @pytest.mark.solver
    # @pytest.mark.skipif(solver is None, reason="Solver not available")
    # @pytest.mark.component
    # def test_conservation(self, model):
    #     assert abs(value(model.fs.unit.inlet.flow_vol[0] -
    #                      model.fs.unit.outlet.flow_vol[0])) <= 1e-6
    #     assert (abs(value(model.fs.unit.inlet.flow_vol[0] *
    #                       sum(model.fs.unit.inlet.conc_mol_comp[0, j]
    #                           for j in model.fs.properties.component_list) -
    #                       model.fs.unit.outlet.flow_vol[0] *
    #                       sum(model.fs.unit.outlet.conc_mol_comp[0, j]
    #                           for j in model.fs.properties.component_list)))
    #             <= 1e-6)

    #     assert (pytest.approx(3904.51, abs=1e-2) == value(
    #             model.fs.unit.control_volume.heat_of_reaction[0]))
    #     assert abs(value(
    #             (model.fs.unit.inlet.flow_vol[0] *
    #              model.fs.properties.dens_mol *
    #              model.fs.properties.cp_mol *
    #              (model.fs.unit.inlet.temperature[0] -
    #                 model.fs.properties.temperature_ref)) -
    #             (model.fs.unit.outlet.flow_vol[0] *
    #              model.fs.properties.dens_mol *
    #              model.fs.properties.cp_mol *
    #              (model.fs.unit.outlet.temperature[0] -
    #               model.fs.properties.temperature_ref)) +
    #             model.fs.unit.control_volume.heat_of_reaction[0])) <= 1e-3

    # @pytest.mark.ui
    # @pytest.mark.unit
    # def test_report(self, model):
    #     model.fs.unit.report()
