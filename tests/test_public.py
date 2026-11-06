import unittest,threading,urllib.request,urllib.error,json
from backend.retrieval import CORPUS,search
from backend.agent import ask
from backend.calculator import cylinder,equal_allocation,arithmetic
from backend.server import Server,Handler
from scripts.import_knowledge import validate
class PublicTests(unittest.TestCase):
    def test_empty_evidence(self):
        self.assertEqual(CORPUS,[]);self.assertEqual(search('误差分配'),[])
        self.assertFalse(ask('误差分配是什么？')['grounded'])
    def test_generic_allocation(self):
        r=equal_allocation(.12,[-1,2,3]);self.assertAlmostEqual(r['recombined'],.12)
        self.assertTrue(all(x>0 for x in r['allocated']))
    def test_original_geometry_case(self):
        r=cylinder(12,30,2,.04,.04)
        self.assertAlmostEqual(r['volume'],3392.928);self.assertAlmostEqual(r['allowed_error'],67.85856)
        self.assertTrue(r['qualified']);self.assertFalse(cylinder(12,30,2,.5,.5)['qualified'])
    def test_safe_arithmetic(self):
        self.assertEqual(arithmetic('sqrt(25+144)')['result'],13)
        with self.assertRaises(Exception):arithmetic('__import__("os").getcwd()')
    def test_no_unverified_import(self):
        with self.assertRaises(ValueError):validate([{'id':'unverified','verified':False}])
        with self.assertRaises(ValueError):validate({'id':'bad'})
    def test_import_with_original_fixture(self):
        row={'id':'demo','title':'自编测试','category':'测试','content':'这是一条自编软件测试数据，不是课程资料。','formula':'','conditions':'','symbols':'','related':[],'verified':True,'sources':[{'file':'self-authored','kind':'自编','chapter':'测试','url':'/demo.html','pdf_page':None,'printed_page':None,'slide':None}]}
        self.assertEqual(validate([row]),[row])
    def test_http_without_course(self):
        server=Server(('127.0.0.1',0),Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        base='http://127.0.0.1:'+str(server.server_address[1])
        try:
            with urllib.request.urlopen(base+'/api/health') as r:self.assertEqual(json.load(r)['chunks'],0)
            with urllib.request.urlopen(base+'/api/exercises') as r:self.assertEqual(json.load(r)['items'],[])
            with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(base+'/.env')
            self.assertEqual(error.exception.code,404)
        finally:server.shutdown();server.server_close()
if __name__=='__main__':unittest.main()
