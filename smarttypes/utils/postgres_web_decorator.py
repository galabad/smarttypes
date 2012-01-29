import smarttypes
from smarttypes.utils.web_response import WebResponse
from smarttypes.utils.exceptions import RedirectException
from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
from smarttypes.model.twitter_session import TwitterSession

def postgres_web_decorator():
    def wrapper0(controller):
        def wrapper1(request):
            postgres_handle = PostgresHandle(smarttypes.connection_string)
            PostgresBaseModel.postgres_handle = postgres_handle
            try:
                session = None
                if request.cookies.get('session'):
                    session = TwitterSession.get_by_request_key(request.cookies['session'])
                response_dict = controller(request, session)
                web_response = WebResponse(request, controller.__name__, response_dict, session)
                response_headers = web_response.get_response_headers()
                response_string = web_response.get_response_str()
                if getattr(postgres_handle, '_connection', False):
                    postgres_handle.connection.commit()
                status_code = '200 OK'
                
            except RedirectException, (redirect_ex):                
                if getattr(postgres_handle, '_connection', False):
                    postgres_handle.connection.commit()
                status_code = '303 See Other'
                response_headers = [('Location', redirect_ex.redirect_url)]
                response_string = [""]
                
            except:
                if getattr(postgres_handle, '_connection', False):
                    postgres_handle.connection.rollback()
                raise
            
            finally:
                if getattr(postgres_handle, '_connection', False):
                    postgres_handle.connection.close() 
            
            #send it all back
            return (status_code, response_headers, response_string) 
        return wrapper1
    return wrapper0