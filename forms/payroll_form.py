from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class DefineSalaryStructureForm(FlaskForm):
    employee_search = StringField('Employee Search', validators=[DataRequired()])
    month = IntegerField('Month', validators=[DataRequired(), NumberRange(min=1, max=12)])  
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1900, max=2100)])
    wday = IntegerField('Working Days', validators=[DataRequired(), NumberRange(min=0)])
    lopd = IntegerField('Leave Without Pay Days', validators=[DataRequired(), NumberRange(min=0)])
    actdays = IntegerField('Actual Days Worked', validators=[DataRequired(), NumberRange(min=0)])
    arrdays = IntegerField('Arrear Days', validators=[DataRequired(), NumberRange(min=0)])
    days_payable = IntegerField('Days Payable', validators=[DataRequired(), NumberRange(min=0)])

    basic_salary = DecimalField('Basic Salary', validators=[DataRequired(), NumberRange(min=0)])
    hra = DecimalField('HRA', validators=[DataRequired(), NumberRange(min=0)])
    special_allowance = DecimalField('Special Allowance', validators=[DataRequired(), NumberRange(min=0)])
    lta = DecimalField('LTA', validators=[DataRequired(), NumberRange(min=0)])
    retention_bonus = DecimalField('Retention Bonus', validators=[DataRequired(), NumberRange(min=0)])
    mobile_internet = DecimalField('Mobile & Internet Allowance', validators=[DataRequired(), NumberRange(min=0)])
    professional_development = DecimalField('Professional Development Allowance', validators=[DataRequired(), NumberRange(min=0)])
    office_attire = DecimalField('Office Attire Allowance', validators=[DataRequired(), NumberRange(min=0)])
    other_allowance = DecimalField('Other Allowance', validators=[DataRequired(), NumberRange(min=0)])
    additional_payment = DecimalField('Additional Payments', validators=[DataRequired(), NumberRange(min=0)])
    additional_bonus = DecimalField('Additional Bonus', validators=[DataRequired(), NumberRange(min=0)])

    pf = DecimalField('PF', validators=[DataRequired(), NumberRange(min=0)])
    vpf = DecimalField('VPF', validators=[DataRequired(), NumberRange(min=0)])
    lwf = DecimalField('LWF', validators=[DataRequired(), NumberRange(min=0)])
    pt = DecimalField('PT', validators=[DataRequired(), NumberRange(min=0)])
    lwf_arrears = DecimalField('LWF Arrears', validators=[DataRequired(), NumberRange(min=0)])
    other_deductions = DecimalField('Other Deductions', validators=[DataRequired(), NumberRange(min=0)])
    tds = DecimalField('TDS', validators=[DataRequired(), NumberRange(min=0)])

    submit = SubmitField('Define Salary Structure')

    def calculate_gross_earnings(self):
        return sum([
            self.basic_salary.data or 0,
            self.hra.data or 0,
            self.special_allowance.data or 0,
            self.lta.data or 0,
            self.retention_bonus.data or 0,
            self.mobile_internet.data or 0,
            self.professional_development.data or 0,
            self.office_attire.data or 0,
            self.other_allowance.data or 0,
            self.additional_payment.data or 0,
            self.additional_bonus.data or 0,
        ])

    def calculate_gross_deductions(self):
        return sum([
            self.pf.data or 0,
            self.vpf.data or 0,
            self.lwf.data or 0,
            self.pt.data or 0,
            self.lwf_arrears.data or 0,
            self.other_deductions.data or 0,
            self.tds.data or 0,
        ])

    def calculate_net_pay(self):
        return self.calculate_gross_earnings() - self.calculate_gross_deductions()
