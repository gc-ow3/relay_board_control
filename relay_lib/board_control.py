from test_comm import testerApi

class boardControl:
    '''
    Communicate with the fixture CPU to set and get IO pin states
    '''
    def __init__(self, fix_api:testerApi, gpio_map:list[dict]=None) -> None:

        '''
        gpio_map is a list of dictionaries each of the form
          "name": "<name of pin>", "gpio_num": <pin number>, "dir": "<out|in>", "active_hi": <True|False>
        '''
        self.fix_api: testerApi = fix_api
        self.gpio_map: list[dict] = gpio_map

    def initialize(self, dbug:bool=False) -> bool:
        '''Configure the controller GPIO pins per the GPIO map'''
        item: dict = dict()
        for item in self.gpio_map:
            gpio_num: int = item['gpio_num']
            # set initial state inactive
            istate: bool = not item.get('active_hi', False)
            if not self.gpio_pin_conf(gpio_num, item['dir'], istate, False, False, dbug=dbug):
                print(f"Failed to configure GPIO {gpio_num}")
                return False
        return True

    def config_set(self, params:dict, dbug:bool=False) -> bool:
        '''
        Set the board configuration

        Parameters
          params - dictionary {"unit_sn": "BOARD_SN", "tty_sn": "FTDI_SN"}

          BOARD_SN is the serial number to assign to the board
          FTDI_SN is the serial number of a FTDI module (if present) on the board

          If the board in question does not have a FTDI module, don't include tty_sn
          in the dictionary.
        '''
        return self.fix_api.command_no_resp("nvs-set", params=params, dbug=dbug)

    def config_get(self, dbug:bool=False) -> dict|None:
        '''Get controller stored parameters'''
        return self.fix_api.command("nvs-get", dbug=dbug)
    
    #
    # CPU GPIO primatives
    # Higher-level functions will build on these
    #

    def gpio_pin_conf(self, gpio_num:int, mode:str, istate:bool, pull_up_en:bool, pull_down_en:bool, dbug:bool=False) -> bool:
        '''Configure a GPIO pin'''
        params = {
            "gpio_num": gpio_num,
            "mode": mode,
            "istate": istate,
            "pull_up_en": pull_up_en,
            "pull_down_en": pull_down_en
        }
        return self.fix_api.command_no_resp("gpio-conf", params=params, dbug=dbug)
    
    def gpio_pin_set(self, gpio_num:int, active:bool, dbug:bool=False) -> bool:
        '''Set the output start of a GPIO pin'''
        return self.fix_api.command_no_resp("gpio-set", params={"gpio_num": gpio_num, "active": active}, dbug=dbug)
    
    def gpio_pin_get(self, gpio_num:int, dbug:bool=False) -> bool|None:
        '''Get the high/low state of a GPIO pin'''
        resp = self.fix_api.command("gpio-get", params={"gpio_num": gpio_num}, dbug=dbug)
        if resp is None:
            return None
        return resp['active']

    def gpio_pin_get_all(self, dbug:bool=False) -> list[dict] | None:
        '''Get the high/low state of each input GPIO pin'''
        resp = self.fix_api.command("gpio-get-all", dbug=dbug)
        if resp is None:
            return None
        return resp

    #
    # Helper functons
    #

    def _find_gpio_desc(self, name:str) -> dict|None:
        '''Lookup the descriptor for the named GPIO'''
        for item in self.gpio_map:
            if name == item['name']:
                return item
        print(f"GPIO descriptor not found for '{name}'")
        return None

    def gpio_set(self, name:str, active:bool, dbug:bool=False) -> bool:
        '''Helper function to set a channel GPIO pin by name'''
        desc: dict = self._find_gpio_desc(name)
        if desc is None:
            return False
        if desc['dir'] != "out":
            print(f"Attempting output on '{name}' which is configured as input")
            return False
        gpio_num: int = desc['gpio_num']
        set_high: bool = active if desc['active_hi'] else not active
        return self.gpio_pin_set(gpio_num, set_high, dbug=dbug)

    def gpio_get(self, name:str, dbug:bool=False) -> bool|None:
        '''Helper function to read a channel GPIO pin by name'''
        desc: dict = self._find_gpio_desc(name)
        if desc is None:
            return None
        if desc['dir'] != "in":
            print(f"Attempting input on '{name}' which is configured as output")
            return None
        gpio_num: int = desc['gpio_num']
        # Get GPIO pin high/low state
        is_high: bool = self.gpio_pin_get(gpio_num, dbug=dbug)
        return is_high if desc['active_hi'] else not is_high
