import math
from itsdangerous import Serializer
import requests
import argparse
from sense_hat import SenseHat

import redis

import pygame

pygame.mixer.init()

sense = SenseHat()

redis_server = redis.Redis(host = 'localhost', port = 6379, decode_responses = True, charset="unicode_escape")

r = (255,0,0)
g = (0,255,0)
b = (0,0,255)
y = (255,200,0)
B = (0,0,0)

idleDisplay = [
    
    g,g,g,g,g,g,g,g,
    g,g,g,g,g,g,g,g,
    g,B,B,g,g,B,B,g,
    g,B,B,g,g,B,B,g,
    g,g,g,B,B,g,g,g,
    g,g,B,B,B,B,g,g,
    g,g,B,B,B,B,g,g,
    g,g,B,g,g,B,g,g,
]

busyDisplay = [
    r,r,r,r,r,r,r,r,
    r,r,r,r,r,r,r,r,
    r,B,B,r,r,B,B,r,
    r,B,B,r,r,B,B,r,
    r,r,r,B,B,r,r,r,
    r,r,B,B,B,B,r,r,
    r,r,B,B,B,B,r,r,
    r,r,B,r,r,B,r,r,
]

waitingDisplay = [
    y,y,y,y,y,y,y,y,
    y,y,y,y,y,y,y,y,
    y,B,B,y,y,B,B,y,
    y,B,B,y,y,B,B,y,
    y,y,y,B,B,y,y,y,
    y,y,B,B,B,B,y,y,
    y,y,B,B,B,B,y,y,
    y,y,B,y,y,B,y,y,
]

deliveredDisplay = [
    
    b,b,b,b,b,b,b,b,
    b,b,b,b,b,b,b,b,
    b,B,B,b,b,B,B,b,
    b,B,B,b,b,B,B,b,
    b,b,b,B,B,b,b,b,
    b,b,B,B,B,B,b,b,
    b,b,B,B,B,B,b,b,
    b,b,B,b,b,B,b,b,
]

def awaitConfirmation():
    sense.set_pixels(waitingDisplay)
    pygame.mixer.music.load("/home/pi/InfoCom-LP3-Lab3/pygame-music/doorbell.mp3")
    pygame.mixer.music.play()
    
    picked_up = False
    while (not picked_up):
        for event in sense.stick.get_events():
            if (event.action == "pressed"):
                
                
                pygame.mixer.music.load("/home/pi/InfoCom-LP3-Lab3/pygame-music/coin.wav")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    continue
                
                picked_up = True
                
                
                
                
        #sense.set_pixels(waitingDisplay)

def getMovement(src, dst):
    speed = 0.00001
    dst_x, dst_y = dst
    x, y = src
    direction = math.sqrt((dst_x - x)**2 + (dst_y - y)**2)
    longitude_move = speed * ((dst_x - x) / direction )
    latitude_move = speed * ((dst_y - y) / direction )
    return longitude_move, latitude_move

def moveDrone(src, d_long, d_la):
    x, y = src
    x = x + d_long
    y = y + d_la        
    return (x, y)

def sessionPost(drone_coords, id, SERVER_URL, status, display):
    with requests.Session() as session:
            drone_info = {'id': id,
                          'longitude': drone_coords[0],
                          'latitude': drone_coords[1],
                          'status': status
                        }
            sense.set_pixels(display)
                 = session.post(SERVER_URL, json=drone_info)

def run(id, current_coords, from_coords, to_coords, SERVER_URL):
    pygame.mixer.music.load("/home/pi/InfoCom-LP3-Lab3/pygame-music/doorbell-1.wav")
    pygame.mixer.music.play()
    drone_coords = current_coords
    d_long, d_la =  getMovement(drone_coords, from_coords)
    while ((from_coords[0] - drone_coords[0])**2 + (from_coords[1] - drone_coords[1])**2)*10**6 > 0.0002:
        drone_coords = moveDrone(drone_coords, d_long, d_la)
        sessionPost(drone_coords, id, SERVER_URL, 'busy', busyDisplay)
        
    sessionPost(drone_coords, id, SERVER_URL, 'waiting', waitingDisplay)
            
    awaitConfirmation()
    
    pygame.mixer.music.load("/home/pi/InfoCom-LP3-Lab3/pygame-music/space-odyssey.mp3")
    pygame.mixer.music.play()
    
    
    d_long, d_la =  getMovement(drone_coords, to_coords)
    while ((to_coords[0] - drone_coords[0])**2 + (to_coords[1] - drone_coords[1])**2)*10**6 > 0.0002:
        drone_coords = moveDrone(drone_coords, d_long, d_la)
        
        
    sessionPost(drone_coords, id, SERVER_URL, 'waiting', waitingDisplay)
            
    awaitConfirmation()
    
    #TODO: Tiden startar
    
    #TODO: Dialogruta
    
    sessionPost(drone_coords, id, SERVER_URL, 'delivered', deliveredDisplay)
    
    #TODO: lägg in två nya vägar, if sats med pressed
    decided = False
    while (not decided):       
        for event in sense.stick.get_events():
            if (event.direction == "down"):
                #Läge missnöjd
                decided = True
                
                d_long, d_la =  getMovement(drone_coords, from_coords)
                while ((from_coords[0] - drone_coords[0])**2 + (from_coords[1] - drone_coords[1])**2)*10**6 > 0.0002:
                    drone_coords = moveDrone(drone_coords, d_long, d_la)
                    sessionPost(drone_coords, id, SERVER_URL, 'busy', busyDisplay)
                            

                sessionPost(drone_coords, id, SERVER_URL, 'waiting', waitingDisplay)        
                awaitConfirmation()
                sessionPost(drone_coords, id, SERVER_URL, 'idle', idleDisplay)
                        
            elif (event.direction == "up"):
                #Läge nöjd
                decided = True
                sessionPost(drone_coords, id, SERVER_URL, 'idle', idleDisplay)
                        
        
            
    redis_server.set('cur_long', drone_coords[0])
    redis_server.set('cur_lat', drone_coords[1])
    
    return drone_coords[0], drone_coords[1]
   
if __name__ == "__main__":
    # Fill in the IP address of server, in order to location of the drone to the SERVER
    #===================================================================
    SERVER_URL = "http://192.168.0.11:5001/drone"
    #===================================================================

    parser = argparse.ArgumentParser()
    parser.add_argument("--clong", help='current longitude of drone location' ,type=float)
    parser.add_argument("--clat", help='current latitude of drone location',type=float)
    parser.add_argument("--flong", help='longitude of input [from address]',type=float)
    parser.add_argument("--flat", help='latitude of input [from address]' ,type=float)
    parser.add_argument("--tlong", help ='longitude of input [to address]' ,type=float)
    parser.add_argument("--tlat", help ='latitude of input [to address]' ,type=float)
    parser.add_argument("--id", help ='drones ID' ,type=str)
    args = parser.parse_args()

    current_coords = (args.clong, args.clat)
    from_coords = (args.flong, args.flat)
    to_coords = (args.tlong, args.tlat)

    print(current_coords, from_coords, to_coords)
    drone_long, drone_lat = run(args.id ,current_coords, from_coords, to_coords, SERVER_URL)
    # drone_long and drone_lat is the final location when drlivery is completed, find a way save the value, and use it for the initial coordinates of next delivery
    #=============================================================================


