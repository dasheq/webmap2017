from . import models

from . import serializers
from rest_framework import permissions
from . import permissions as my_permissions
from wmap2017 import settings
from django.contrib.gis.db import models
from models import FriendGroup
from django.contrib.auth import authenticate, login, logout, get_user_model
from rest_framework import permissions, authentication, status, generics
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry, LineString, Point, Polygon
from rest_framework.authtoken.models import Token
# from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.forms import ValidationError
import urllib as urllib2




from . import forms


class UsersList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserOtherSerializer

    def get_queryset(self):
        return get_user_model().objects.all().order_by("username")

    def get_serializer_context(self):
        return {"request": self.request}


class UserMe_R(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserMeSerializer

    def get_object(self):
        return get_user_model().objects.get(email=self.request.user.email)


class UserOther_R(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        if "uid" in self.kwargs and self.kwargs["uid"]:
            users = get_user_model().objects.filter(id=self.kwargs["uid"])
        elif "email" in self.kwargs and self.kwargs["email"]:
            users = get_user_model().objects.filter(email=self.kwargs["email"])
        else:
            users = None
        if not users:
            self.other = None
            raise exceptions.NotFound
        self.other = users[0]
        return self.other

    def get_serializer_class(self):
        if self.request.user == self.other:
            return serializers.UserMeSerializer
        else:
            return serializers.UserOtherSerializer


class UpdatePosition(generics.UpdateAPIView):
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserMeSerializer

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(UpdatePosition, self).dispatch(*args, **kwargs)

    def get_object(self):
        return get_user_model().objects.get(email=self.request.user.email)

    def perform_update(self, serializer, **kwargs):
        try:
            lat1 = float(self.request.data.get("lat", False))
            lon1 = float(self.request.data.get("lon", False))
            # lat2 = float(self.request.query_params.get("lat", False))
            # lon2 = float(self.request.query_params.get("lon", False))
            if lat1 and lon1:
                point = Point(lon1, lat1)
            # elif lat2 and lon2:
            #     point = Point(lon2, lat2)
            else:
                point = None

            if point:
                # serializer.instance.last_location = point
                serializer.save(last_location = point)
            return serializer
        except:
            pass


@api_view(["GET", ])
@permission_classes((permissions.AllowAny,))
# @csrf_exempt
def token_login(request):
    if (not request.GET["username"]) or (not request.GET["password"]):
        return Response({"detail": "Missing username and/or password"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=request.GET["username"], password=request.GET["password"])
    if user:
        if user.is_active:
            login(request, user)
            try:
                my_token = Token.objects.get(user=user)
                return Response({"token": "{}".format(my_token.key)}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"detail": "Could not get token"})
        else:
            return Response({"detail": "Inactive account"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"detail": "Invalid User Id of Password"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET", ])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def register(request):
    print (request.GET)

    print("first bp hit")
    if (not request.GET["username"]) or (not request.GET["password"] or (not request.GET["email"])):
        return Response({"detail": "Missing username and/or password and/or email"}, status=status.HTTP_400_BAD_REQUEST)
        print("no values")
    try:
        user = get_user_model().objects.get(username=request.GET["username"])
        if user:
            print("user already exists")
            return Response({"detail": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
    except get_user_model().DoesNotExist:
        user = get_user_model().objects.create_user(username=request.GET["username"])

        # Set user fields provided
        print(request.GET["password"] + request.GET["firstname"] + request.GET["lastname"] + request.GET["email"])
        user.set_password(request.GET["password"])
        user.first_name = request.GET["firstname"]
        user.last_name = request.GET["lastname"]
        user.email = request.GET["email"]
        user.save()
        print("done")

        return Response({"detail": "Successfully created"}, status=status.HTTP_201_CREATED)




@api_view(["GET", ])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def show_locations(request):
    file = urllib2.urlopen(
        'https://data.dublinked.ie/dataset/b1a0ce0a-bfd4-4d0b-b787-69a519c61672/resource/b38c4d25-097b-4a8f-b9be-cf6ab5b3e704/download/walk-dublin-poi-details-sample-datap20130415-1449.json')
    data = file.read()
    file.close()

    return Response({"data": data}, status=status.HTTP_200_OK)


@api_view(["GET", ])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def show_groups(request):
    user = get_user_model().objects.get(username=request.GET["owner"])
    groups = FriendGroup.objects.filter(owner=user).values('name')

    print(groups)
    return Response({"data": groups},status=status.HTTP_200_OK)

@api_view(["GET", ])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def create_group(request):
    groupname = request.GET["name"]
    groupowner = request.GET["owner"]

    if (not groupname) or (not groupowner):
        return Response({"detail": "Missing groupname"}, status=status.HTTP_400_BAD_REQUEST)
        print("no values")

    group = models.FriendGroup()
    group.name = groupname
    group.owner = groupowner
    group.save()

    return Response({"detail": "Successfully created"}, status=status.HTTP_201_CREATED)

@api_view(["GET", ])
@permission_classes((permissions.AllowAny,))
@csrf_exempt
def show_friends(request):
    username = request.GET['username']
    groupname = request.GET['groupname']

    group = FriendGroup.objects.get(owner=username, name=groupname)

    friends = list(UserFriendGroup.objects.filter(friend_group=group).values("member_id"))

    friendList = []
    for member in friends:
        user = get_user_model().objects.get(id=member["member_id"]).get_username()
        friendList.append(user)

    friendList = list(friendList)
    list = [s.encode('utf-8') for s in friendList]

    return Response({"friendList": list}, status=status.HTTP_200_OK)

