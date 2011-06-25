#ifndef NPROB_HPP
#define NPROB_HPP


#include <cmath>
#define pi 3.14152965

/**

 Porbability distribution helper functions written by Danny Bickson, CMU


*/

using namespace itpp;
using namespace std;

//#define WISHART_TEST
//#define WISHART_TEST2

/* (C) Copr. 1986-92 Numerical Recipes Software 0NL-Z%. */

float gamdev(int ia)
{
	int j;
	float am,e,s,v1,v2,x,y;

	assert(ia>=1);
        if (ia < 6) {
		x=1.0;
		for (j=1;j <= ia;j++) x *= drand48();
		x = -log(x);
	} else {
		do {
			do {
				do {
					v1=drand48();
					v2=2.0*drand48()-1.0;
				} while (v1*v1+v2*v2 > 1.0);
				y=v2/v1;
				am=ia-1;
				s=sqrt(2.0*am+1.0);
				x=s*y+am;
			} while (x <= 0.0);
			e=(1.0+y*y)*exp(am*log(x/am)-s*y);
		} while (drand48() > e);
	}
	return x;
}

vec chi2rnd(vec v, int size){

  vec ret = zeros(size);
  for (int i=0; i<size; i++)
     ret[i] = 2.0* gamdev(v[i]/2.0); //TODO

#ifdef WISHART_TEST
  ret = vec("9.3343    9.2811    9.3583    9.3652    9.3031");
  ret*= 1e+04;
#elif defined(WISHART_TEST2)
  ret = vec("4.0822e+03");
#endif
  return ret;

}

void randv(int n, vec & ret){
   assert(n>=1);
   for (int i=0; i< n; i++)
       ret[i] = drand48();
}

mat randn1(int Dx, int Dy){
  if (Dx == 0)
    Dx = 1;
  assert(Dy>=1);
  mat ret = zeros(Dx,Dy);
  vec us = zeros(ceil(Dx*Dy/2.0)*2); 
  randv(ceil(Dx*Dy/2.0)*2, us);
  int k=0;
  for (int i=0; i<Dx; i++){
     for (int j=0; j< Dy; j++){
         if (k % 2 == 0)
         	ret(i,j) = sqrt(-2.0*std::log(us[k/2]))*std::cos(2*pi*us[k/2+1]);
         else
         	ret(i,j) = sqrt(-2.0*std::log(us[k/2]))*std::sin(2*pi*us[k/2+1]);
         k++;
     }
  }
  assert(k == Dx*Dy);
  assert(ret.rows() == Dx && ret.cols() == Dy);
  return ret;
}

vec mvnrndex(vec &mu, mat &sigma, int d){
   assert(mu.size() == d);
   bool ret;
   mat tmp;
   ret = itpp::chol(sigma, tmp);
   assert(ret);
   vec x = zeros(d);
   vec col = randn1(mu.size(), 1).get_col(0);
   x = mu + transpose(tmp) * col;
   assert(x.size() == d);
   return x;
}

mat load_itiru(mat &a, mat& b){
   assert(a.size() >= 1);
   //nothing to do in case of a scalar
   if (a.rows() == 1 && a.cols() == 1)
       return a;

   assert(b.cols() == 1);
   assert(a.rows() == a.cols());
   int n = a.rows();
   int k = 0;
   for (int i=0; i< n; i++)
     for (int j=i+1; j< n; j++){
        a.set(i,j, b.get(k++,0));
     } 
   assert(k == (n*(n-1))/2.0);
   return a;
}

vec sequence(int df, int n){
   assert(n >= 1);
   assert(df>= 0);
 
   vec ret(n);
   for (int i=0; i<n; i++)
     ret[i] = df - i;

   return ret;
}


mat wishrnd(mat& sigma, double df){

   mat d;
   //cout<<sigma<<endl;
   bool ret = chol(sigma, d);
   //cout<<d<<endl;
   assert(ret);
   int n = sigma.rows();
   mat x = zeros(n,n) ,a = zeros(n,n);
   mat b;

   if ((df <= 81+sigma.rows()) && (df == itpp::round(df))){
       x = randn((int)df, d.rows())*d;
   }
   else {
       vec seq = sequence(df, n);
       //cout<<seq<<endl;
       vec ret = chi2rnd(seq, n);
       //cout<<ret<<endl;
       ret = sqrt(ret);
       //assert(ret.size() == n);
       //cout<<ret<<endl;
       if (ret.size() == 1) // a scalar variable
           a.set(0,0, ret[0]);
       else //a matrix 
           a = diag(ret); //TODO: df-(0:n-1) 
       
       assert(a.rows() == n && a.cols() == n); 
       //cout<<a<<endl;
      
       if (ret.size() > 1){
         b = randn(n*(n-1)/2,1);
         assert(b.cols() == 1);
       }
#ifdef WISHART_TEST
  b=zeros(10,1); b = mat("0.1139  ;  1.0668 ;  -0.0956 ;  -1.3362; 0.0593 ;  -0.8323  ;  0.7143;     0.2944 ;   1.6236; -0.6918");
  //b = zeros(10,1); b = mat(" 1.1909 ; 1.1892 ; -0.0376;  0.3273; 0.1746; -0.1867; 0.7258; -0.5883; 2.1832; -0.1364");
#elif defined(WISHART_TEST2)
  b = mat(0,0);
#endif

       if (ret.size() > 1)
          a = load_itiru(a,b);
       //assert(a.rows() == n && a.cols() == n); 
       //cout<<a<<endl;
       x = a*d;
       //assert(x.cols() == x.rows() && x.cols() == n);
       //cout<<x<<endl;
   }

   mat c= transpose(x)*x;
   assert(c.rows() == n && c.cols() == n); 
   //cout<<a<<endl;
   //
   assert(sumsum(abs(c))!= 0);
   return c;
}

void test_wishrnd(){
  #ifndef WISHART_TEST
     assert(false);
  #endif
   mat a = zeros(5,5); 
    a = mat(" 0.2977   -0.0617   -0.1436   -0.0929    0.0136;"
   "-0.0617    0.3489   -0.0736   -0.0581   -0.1337;"
   "-0.1436   -0.0736    0.4457   -0.0348   -0.0301;"
   "-0.0929   -0.0581   -0.0348    0.3165    0.0029;"
   " 0.0136   -0.1337   -0.0301    0.0029    0.1862;");
   assert(a.rows() == a.cols() && a.rows() == 5);
   a *= 1.0e-03;

   int df = 93531;

   mat b = wishrnd(a,df);
   mat trueret("  27.7883   -5.6442  -13.3231   -8.7063    1.2395;"
   "-5.6442   32.3413   -6.8909   -5.3947  -12.4362;"
  "-13.3231   -6.8909   41.5932   -3.3148   -2.6792;"
  " -8.7063   -5.3947   -3.3148   29.6388    0.2115;"
   " 1.2395  -12.4362   -2.6792    0.2115   17.3015;");
   double diff = sumsum(b-trueret)/(25.0);
   assert(fabs(diff) < 1e-2);
 
}
void test_wishrnd2(){
  #ifndef WISHART_TEST2
     assert(false);
  #endif

   mat a("3");
   assert(a.rows() == a.cols() && a.rows() == 1);
   int df = 4122;

   mat b = wishrnd(a,df);
   mat trueret("1.2247e+04");
   double diff = sumsum(b-trueret);
   assert(fabs(diff) < 1);
 
}

void test_randn(){
#if (defined(WISHART_TEST2) || defined(WISHART_TEST))
   assert(false);
#endif  
 
   mat a = randn(10000000,1);
   double ret = fabs(sumsum(a)/10000000);
   assert(ret < 4e-3);
   ret = fabs(variance(a.get_col(0)) - 1);
   assert(ret < 1e-3);

}

void test_mvnrndex(){

  mat sigma = 
 " 0.990566133945187  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813   0.990566133945187  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813   0.990566133945187  -0.009433866054813  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813  -0.009433866054813   0.990566133945187  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813   0.990566133945187  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813   0.990566133945187 ";
  vec mu = "95532 -1 2 3 0 22";
  
  vec ret = zeros(6);
  for (int i=0; i<10000; i++){
    ret+= mvnrndex(mu,sigma,6);
  }
  ret /= 10000;

  vec ans = "95532.0115    -0.996855354      2.00914034      2.99521376   -0.0105874825      22.0127606";
  cout<<ret<<endl<<norm(ans-ret)<<endl;


}




void test_chi2rnd(){
   vec ret = zeros(6);
   vec v = vec("95532 95531 95530 95529 95528 95527");
   for  (int i=0; i< 1000000; i++){
     ret += chi2rnd(v, 6);
   }
  ret /= 1000000;
  vec ans = "95531.99 95531.672 95530.016 95530.005 95527.495 95527.447";
  cout<<ret<<endl<<norm(ans-ret)<<endl;

}

void test_wishrnd3(){

  mat sigma = 
 " 0.990566133945187  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813   0.990566133945187  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813   0.990566133945187  -0.009433866054813  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813  -0.009433866054813   0.990566133945187  -0.009433866054813  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813   0.990566133945187  -0.009433866054813 ;" \
 " -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813  -0.009433866054813   0.990566133945187 ";
  int df = 95532;
  
  mat ret = zeros(6,6);
  for (int i=0; i<10000; i++){
    ret+= wishrnd(sigma, df);
  }
  ret /= 10000;

  mat ans = "9.463425666451165  -0.090326102576222  -0.091016693707751  -0.089933822069320  -0.090108095540542  -0.089915220156678 ;\
  -0.090326102576222   9.462305273959634  -0.090071105888907  -0.090355541326424  -0.090556802227637  -0.089887181087950 ;\
  -0.091016693707751  -0.090071105888907   9.462973812711439  -0.090185140101184  -0.090013352917616  -0.089803917691135 ;\
  -0.089933822069320  -0.090355541326424  -0.090185140101184   9.462292292298272  -0.090233918216433  -0.090557276073727 ;\
  -0.090108095540542  -0.090556802227637  -0.090013352917616  -0.090233918216433   9.461377045031403  -0.089774502028808 ;\
  -0.089915220156678  -0.089887181087950  -0.089803917691135  -0.090557276073727  -0.089774502028808   9.463220187604252";
  ans *= 1.0e+04;

  cout<<ret<<endl<<norm(ans-ret)<<endl;
}









#endif //NPROB_HPP
