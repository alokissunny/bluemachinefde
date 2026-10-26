import math, tempfile, unittest
from pathlib import Path
import server

class ServicingTests(unittest.TestCase):
    def test_emi_amortizes_to_zero(self):
        balance=server.P
        for _ in range(server.MONTHS): balance=balance*(1+server.RATE/12)-server.emi(server.P,server.RATE,server.MONTHS)
        self.assertAlmostEqual(balance,0,places=6)
    def test_savings_match_independent_closed_form(self):
        r=server.RATE/12; payment=server.emi(server.P,server.RATE,server.MONTHS); amount=50000
        remaining=server.P-amount
        n=math.ceil(-math.log(1-remaining*r/payment)/math.log(1+r))
        for _ in range(n-1): remaining=remaining*(1+r)-payment
        final=remaining*(1+r)
        expected=(payment*42-server.P)-((n-1)*payment+final-(server.P-amount))
        result=server.simulate(amount)
        self.assertEqual(result['new_months'],n)
        self.assertAlmostEqual(result['interest_saved'],expected,places=2)
    def test_invalid_amounts(self):
        for amount in [0,-1,server.P,float('inf'),float('nan')]:
            with self.assertRaises(ValueError): server.simulate(amount)
    def test_followup_retains_amount(self):
        s={}; a=server.query(s,'What if I prepay 50000?','loans',False,False)
        b=server.query(s,'What about 20000 instead?','loans',False,False)
        self.assertEqual(a['result']['amount'],50000)
        self.assertEqual(b['result']['amount'],20000)
        self.assertGreater(a['result']['interest_saved'],b['result']['interest_saved'])
    def test_invalid_amount_is_not_replaced_by_default(self):
        for text in ['prepay 0', 'prepay -100']:
            result=server.query({},text,'loans',False,False)
            self.assertIsNone(result['action'])
            self.assertIsNone(result['result'])
    def test_failed_source_never_invents_status(self):
        result=server.query({},'show failed payments','loans',True,False)
        self.assertFalse(result['trace']['ok'])
        self.assertIsNone(result['action'])
        self.assertEqual(result['sources'],[])
    def test_second_workflow_uses_confirmation_token(self):
        s={}; result=server.query(s,'Dispute this card transaction','cards',False,False)
        self.assertEqual(result['action']['kind'],'Card dispute')
        self.assertEqual(result['action']['token'],s['pending']['token'])
    def test_new_intent_invalidates_prior_action(self):
        s={}; server.query(s,'prepay 50000','loans',False,False)
        server.query(s,'next EMI','loans',False,False)
        self.assertNotIn('pending',s)

if __name__=='__main__': unittest.main()
