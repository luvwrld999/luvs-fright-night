#---------------------------------------------------------------------------------------------------------------------
# Luv's Fright Night - GBA platformer (Butano / devkitARM)
# Built inside the devkitpro/devkitarm container: see ./build.sh
#---------------------------------------------------------------------------------------------------------------------
TARGET      	:=  LuvsFrightNight
BUILD       	:=  build
LIBBUTANO   	:=  butano/butano
PYTHON      	:=  python3
SOURCES     	:=  src butano/common/src
INCLUDES    	:=  include butano/common/include
DATA        	:=
GRAPHICS    	:=  graphics butano/common/graphics
AUDIO       	:=  audio
AUDIOBACKEND	:=  maxmod
AUDIOTOOL		:=
DMGAUDIO    	:=
DMGAUDIOBACKEND	:=  null
ROMTITLE    	:=  LUVSFRIGHT
ROMCODE     	:=  LFNE
USERFLAGS   	:=  -DBN_CFG_ASSERT_ENABLED=true -DBN_CFG_AUDIO_MAX_SOUND_CHANNELS=8 -DBN_CFG_AUDIO_MAX_COMMANDS=32 -DBN_CFG_SPRITE_TILES_MAX_ITEMS=256 -DBN_CFG_SPRITES_MAX_ITEMS=192 -DBN_CFG_SPRITE_PALETTES_MAX_ITEMS=32
USERCXXFLAGS	:=
USERASFLAGS 	:=
USERLDFLAGS 	:=
USERLIBDIRS 	:=
USERLIBS    	:=
DEFAULTLIBS 	:=
STACKTRACE		:=
USERBUILD   	:=
EXTTOOL     	:=

#---------------------------------------------------------------------------------------------------------------------
# Export absolute butano path:
#---------------------------------------------------------------------------------------------------------------------
ifndef LIBBUTANOABS
	export LIBBUTANOABS	:=	$(realpath $(LIBBUTANO))
endif

#---------------------------------------------------------------------------------------------------------------------
# Include main makefile:
#---------------------------------------------------------------------------------------------------------------------
include $(LIBBUTANOABS)/butano.mak
