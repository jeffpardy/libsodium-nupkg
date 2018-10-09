using System;
using System.Runtime.InteropServices;

internal static class Program
{
    [DllImport("libsodium", CallingConvention = CallingConvention.Cdecl)]
    internal static extern int sodium_init();

    [DllImport("libsodium", CallingConvention = CallingConvention.Cdecl)]
    internal static extern int sodium_library_version_major();

    [DllImport("libsodium", CallingConvention = CallingConvention.Cdecl)]
    internal static extern int sodium_library_version_minor();

    internal static int Main()
    {
        Console.Write("sodium_library_version_major() = ");
        Console.WriteLine(sodium_library_version_major());

        Console.Write("sodium_library_version_minor() = ");
        Console.WriteLine(sodium_library_version_minor());

        Console.Write("sodium_init() = ");
        int error = sodium_init();
        Console.WriteLine(error);
        return error == 0 ? 0 : 1;
    }
}
