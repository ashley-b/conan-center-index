#include <array>
#include <cstdio>
#include <volk/volk.h>

int main()
{
    printf("Volk Version %s\n", volk_version());
    printf("volk Available Machines %s\n", volk_available_machines());
    lv_32fc_t result;
    const lv_32fc_t input;
    std::array< float, 8 > taps;
    volk_32fc_32f_dot_prod_32fc_u(&result, &input, taps.data(), taps.size());
    return 0;
}
